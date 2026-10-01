import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_cytoscape as cyto
import py_trees
import base64
import os

# ==============================================================================
# 1. 后端：构建标准的 py_trees 行为树与黑板
# ==============================================================================
# 注册全局黑板（用于网页前端与后端树交换数据）
blackboard = py_trees.blackboard.Client(name="WebPlatform")
blackboard.register_key(key="file_uploaded", access=py_trees.common.Access.WRITE)
blackboard.register_key(key="file_uploaded", access=py_trees.common.Access.READ)
blackboard.file_uploaded = False  # 初始状态：未上传

# 定义节点 A：检查文件是否上传
class CheckFileNode(py_trees.behaviour.Behaviour):
    def __init__(self, name="n1"):
        super(CheckFileNode, self).__init__(name)
    def update(self):
        if blackboard.file_uploaded:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE

# 定义节点 B：后台耗时任务
class HeavyTaskNode(py_trees.behaviour.Behaviour):
    def __init__(self, name="n2"):
        super(HeavyTaskNode, self).__init__(name)
        self.ticks_count = 0
    def initialise(self):
        self.ticks_count = 0
    def update(self):
        self.ticks_count += 1
        if self.ticks_count < 4:  # 模拟执行需要多次 Tick 才能完成（约4秒）
            return py_trees.common.Status.RUNNING
        return py_trees.common.Status.SUCCESS

# 组装并初始化行为树
root_tree = py_trees.composites.Sequence(name="MainTree", memory=True)
root_tree.add_children([CheckFileNode("n1"), HeavyTaskNode("n2")])
root_tree.setup_with_descendants()

# 定义前端图形的数据模型（对应行为树节点 ID）
graph_elements = [
    {"data": {"id": "n1", "label": "1. 上传报销单 (点击上传)", "nodeType": "upload"}},
    {"data": {"id": "n2", "label": "2. AI 自动核验 (长期任务)", "nodeType": "task"}},
    {"data": {"source": "n1", "target": "n2"}},
]

# ==============================================================================
# 2. 前端：使用 Python Dash 布局 (Layout)
# ==============================================================================
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("纯 Python 行为树工作流交互系统", style={"textAlign": "center", "marginBottom": "30px"}),
    
    # 定时器：每 1 秒触发一次，让后端行为树自动 Tick 并让前端刷新状态
    dcc.Interval(id="tree-ticker", interval=1000, n_intervals=0),
    
    html.Div([
        # 左侧：流程图画布
        html.Div([
            cyto.Cytoscape(
                id="cytoscape-workflow",
                elements=graph_elements,
                layout={"name": "grid", "columns": 1},  # 垂直排列
                style={"width": "100%", "height": "450px", "border": "1px solid #ccc", "borderRadius": "8px"},
                stylesheet=[
                    # 默认节点样式 (对应 py_trees.common.Status.INVALID 或未运行状态)
                    {"selector": "node", "style": {"content": "data(label)", "text-valign": "center", "shape": "round-rectangle", "width": "220px", "height": "50px", "background-color": "#95a5a6", "color": "white", "font-size": "14px"}},
                    {"selector": "edge", "style": {"curve-style": "bezier", "target-arrow-shape": "triangle", "line-color": "#7f8c8d"}},
                    # 行为树不同生命周期状态的视觉定义
                    {"selector": ".success", "style": {"background-color": "#2ecc71"}},  # 成功变绿
                    {"selector": ".running", "style": {"background-color": "#3498db"}},  # 运行变蓝
                    {"selector": ".failure", "style": {"background-color": "#e74c3c"}},  # 失败变红
                ]
            )
        ], style={"width": "60%", "display": "inline-block", "verticalAlign": "top"}),
        
        # 右侧：点击节点后弹出的侧边操作面板
        html.Div([
            html.H3("节点控制中心"),
            html.Div(id="control-panel-content", children="请在左侧点击流程图节点以开始操作。")
        ], style={"width": "35%", "display": "inline-block", "marginLeft": "4%", "padding": "20px", "border": "1px dashed #7f8c8d", "borderRadius": "8px", "minHeight": "200px"})
    ]),
], style={"fontFamily": "Segoe UI, sans-serif", "padding": "40px"})

# ==============================================================================
# 3. 核心桥接：交互与状态刷新的 Dash 回调 (Callbacks)
# ==============================================================================

# 回调 1：处理左侧节点的点击事件，动态在右侧控制中心生成交互组件
@app.callback(
    Output("control-panel-content", "children"),
    Input("cytoscape-workflow", "tapNodeData")
)
def render_control_panel(node_data):
    if not node_data:
        return "请在左侧点击流程图节点以开始操作。"
    
    node_id = node_data["id"]
    node_type = node_data["nodeType"]
    label = node_data["label"]
    
    content = [html.H4(f"已选中步骤: {label}")]
    
    if node_type == "upload":
        content.extend([
            html.P("此步骤需要您上传发票或文件才能继续："),
            dcc.Upload(
                id="dash-file-uploader",
                children=html.Button("选择并上传文件", style={"padding": "10px 20px", "backgroundColor": "#2ecc71", "color": "white", "border": "none", "cursor": "pointer"}),
                multiple=False
            ),
            html.Div(id="upload-output-msg", style={"marginTop": "10px", "color": "#27ae60"})
        ])
    elif node_type == "task":
        content.extend([
            html.P("这是一个由系统自动运行的 AI 分析脚本。当步骤 1 成功后，它会在后台自动触发。")
        ])
        
    return content

# 回调 2：处理上传动作，一旦文件上传成功，写入 py_trees 行为树的 Blackboard
@app.callback(
    Output("upload-output-msg", "children"),
    Input("dash-file-uploader", "contents"),
    State("dash-file-uploader", "filename"),
    prevent_initial_call=True
)
def handle_file_upload(contents, filename):
    if contents:
        # 解码并保存文件（此处仅做演示，实际可写入磁盘）
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # 【核心同步】更改行为树黑板变量，通知 py_trees 文件已就绪！
        blackboard.file_uploaded = True
        return f"✓ 成功上传 {filename}，已通知后端行为树！"
    return ""

# 回调 3：核心轮询驱动引擎！每秒驱动行为树 Tick 响应，并将各个节点的最新状态反映到前端颜色上
@app.callback(
    Output("cytoscape-workflow", "stylesheet"),
    Input("tree-ticker", "n_intervals"),
    State("cytoscape-workflow", "stylesheet")
)
def update_tree_status_visually(n, current_stylesheet):
    # 1. 驱动后台 py_trees 行为树进行一次心跳 Tick
    root_tree.tick_once()
    
    # 2. 获取树中各个自定义节点最新的行为树状态
    # py_trees 状态包括：SUCCESS, RUNNING, FAILURE, INVALID
    status_map = {}
    for child in root_tree.children:
        status_map[child.name] = child.status.name
        
    # 3. 动态构建前端样式表（通过给对应的节点添加样式类名）
    # 我们保留初始的基础样式，并为变动的节点动态叠加特殊的 class 样式
    base_style = [
        {"selector": "node", "style": {"content": "data(label)", "text-valign": "center", "shape": "round-rectangle", "width": "220px", "height": "50px", "background-color": "#95a5a6", "color": "white"}},
        {"selector": "edge", "style": {"curve-style": "bezier", "target-arrow-shape": "triangle", "line-color": "#7f8c8d"}},
    ]
    
    for node_id, status in status_map.items():
        if status == "SUCCESS":
            base_style.append({"selector": f"node[id='{node_id}']", "style": {"background-color": "#2ecc71"}}) # 绿色
        elif status == "RUNNING":
            base_style.append({"selector": f"node[id='{node_id}']", "style": {"background-color": "#3498db"}}) # 蓝色
        elif status == "FAILURE":
            # 注意：在 Sequence 逻辑中，如果前置节点为 FAILURE，则后置节点通常处于 INVALID 灰色状态
            base_style.append({"selector": f"node[id='{node_id}']", "style": {"background-color": "#e74c3c"}}) # 红色

    return base_style

if __name__ == "__main__":
    # 使用现代 Dash 标准的 app.run 启动服务器
    app.run(debug=True)
