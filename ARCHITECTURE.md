# Text-to-CAD 系统架构设计文档

## 项目概述

一个基于大型语言模型的自然语言转 CAD 系统，用户通过网页输入自然语言描述，系统自动生成可导出、可预览的 STEP 格式 3D 模型。

---

## 1. 系统整体架构设计

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端层 (Frontend)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Prompt输入   │  │  任务状态面板  │  │  3D模型预览   │  │  历史任务列表     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
│         │                 │                 │                    │          │
└─────────┼─────────────────┼─────────────────┼────────────────────┼──────────┘
          │                 │                 │                    │
          └─────────────────┴─────────────────┴────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway                                      │
│                    (FastAPI / Express + WebSocket)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   任务队列服务   │ │    文件存储     │ │   实时通知服务   │
│   (Celery/     │ │   (S3/MinIO)   │ │   (WebSocket/  │
│    RabbitMQ)   │ │                │ │    SSE)        │
└────────┬────────┘ └────────────────┘ └────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           核心处理引擎层                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        任务编排服务 (Task Orchestrator)              │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │   │
│  │  │ 需求解析器  │ │ 复杂度评估  │ │ 任务拆分器  │ │ 任务调度器  │  │   │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘  │   │
│  │         │               │               │               │         │   │
│  │         └───────────────┴───────────────┴───────────────┘         │   │
│  │                             │                                      │   │
│  │                             ▼                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │                  LLM 建模规划模块                            │  │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │  │   │
│  │  │  │ 提示词工程  │ │ 结构化输出  │ │ 代码/JSON 生成     │   │  │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CAD 几何执行引擎                                 │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │ JSON Schema │ │ 代码生成器  │ │ CadQuery    │ │ STEP 导出   │   │   │
│  │  │ 验证器      │ │ (Python)    │ │ 执行器      │ │ 模块        │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     预览转换服务                                     │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │   │
│  │  │ STEP→STL   │ │ STL→glTF   │ │ 网格优化    │                    │   │
│  │  │ 转换器     │ │ 转换器      │ │ 处理        │                    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据存储层                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                  │
│  │  PostgreSQL    │  │     Redis      │  │   MinIO/S3     │                  │
│  │  (任务/用户)   │  │  (缓存/队列)   │  │  (文件存储)    │                  │
│  └────────────────┘  └────────────────┘  └────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件说明

| 组件 | 职责 | 技术选型 |
|------|------|----------|
| **前端** | 用户交互、3D预览、状态展示 | React + TypeScript + React Three Fiber |
| **API Gateway** | 路由、认证、限流 | FastAPI (Python) |
| **任务队列** | 异步任务处理 | Celery + Redis |
| **任务编排器** | 解析、评估、拆分、调度任务 | Python 服务 |
| **LLM模块** | 自然语言理解、建模规划 | Claude / GPT-4 + 结构化输出 |
| **CAD引擎** | 几何建模、STEP导出 | CadQuery (OpenCascade) |
| **预览转换** | STEP→glTF 转换 | Python 脚本 + meshio |
| **存储** | 数据持久化、文件存储 | PostgreSQL + Redis + MinIO |

---

## 2. 网页交互设计

### 2.1 页面流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           首页 / 登录                                │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     主设计界面                                  │  │
│  │                                                               │  │
│  │   ┌──────────────────────────────────────────────────────┐   │  │
│  │   │  🔧 Text-to-CAD 智能建模系统                          │   │  │
│  │   │                                                       │   │  │
│  │   │   描述你想要创建的零件...                              │   │  │
│  │   │   ┌────────────────────────────────────────────────┐ │   │  │
│  │   │   │ 创建一个铝合金支架，底部是100x80mm的矩形板，     │ │   │  │
│  │   │   │ 厚度5mm，四角有M6螺栓孔，中心有一个直径30mm的圆孔  │ │   │  │
│  │   │   └────────────────────────────────────────────────┘ │   │  │
│  │   │                                                       │   │  │
│  │   │   [高级选项 ▼]              [🚀 开始生成]            │   │  │
│  │   └──────────────────────────────────────────────────────┘   │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     生成中界面                                  │  │
│  │                                                               │  │
│  │   ┌──────────────────────────────────────────────────────┐   │  │
│  │   │  正在生成您的设计...                                    │   │  │
│  │   │                                                       │   │  │
│  │   │  ┌──────────────┐                                      │   │  │
│  │   │  │ [==========>  ] 65%                                 │   │  │
│  │   │  └──────────────┘                                      │   │  │
│  │   │                                                       │   │  │
│  │   │  ✅ 需求解析完成                                        │   │  │
│  │   │  ✅ 复杂度评估: 中等                                     │   │  │
│  │   │  ⏳ 生成建模计划 (3/5 步骤)                              │   │  │
│  │   │     └─ 正在创建底部矩形板...                             │   │  │
│  │   │  ⬜ 执行CAD建模                                         │   │  │
│  │   │  ⬜ 导出STEP文件                                        │   │  │
│  │   │  ⬜ 生成预览模型                                        │   │  │
│  │   │                                                       │   │  │
│  │   │  [查看详细日志]  [取消]                                │   │  │
│  │   └──────────────────────────────────────────────────────┘   │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     结果展示界面                                │  │
│  │                                                               │  │
│  │   ┌──────────────┬─────────────────────────────────────────┐  │  │
│  │   │              │                                         │  │  │
│  │   │   3D预览     │     📊 模型信息                          │  │  │
│  │   │    viewport  │     ─────────────────                     │  │  │
│  │   │              │     体积: 128.5 cm³                      │  │  │
│  │   │    [旋转     │     表面积: 452.3 cm²                    │  │  │
│  │   │     缩放     │     尺寸: 100×80×12 mm                   │  │  │
│  │   │     平移]    │     格式: STEP (AP214)                   │  │  │
│  │   │              │                                         │  │  │
│  │   │              │     🔧 建模步骤                          │  │  │
│  │   │              │     1. 创建底部矩形板                     │  │  │
│  │   │              │     2. 添加四角螺栓孔                     │  │  │
│  │   │              │     3. 添加中心圆孔                       │  │  │
│  │   │              │     4. 应用倒角                          │  │  │
│  │   │              │                                         │  │  │
│  │   │              │     [⬇️ 下载STEP]  [🔄 重新生成]        │  │  │
│  │   │              │     [📋 查看JSON方案]                     │  │  │
│  │   └──────────────┴─────────────────────────────────────────┘  │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 UI 组件设计规范

**颜色主题（工程风格）**
```css
--primary: #2563eb;        /* 工程蓝 */
--secondary: #64748b;      /*  slate灰 */
--success: #10b981;        /* 成功绿 */
--warning: #f59e0b;        /* 警告橙 */
--error: #ef4444;          /* 错误红 */
--background: #0f172a;     /* 深蓝黑背景 */
--surface: #1e293b;        /* 卡片表面 */
--text-primary: #f8fafc;   /* 主文本白 */
--text-secondary: #94a3b8; /* 次文本灰 */
```

**字体**
- 主字体: Inter / system-ui
- 代码/数据: JetBrains Mono / Fira Code

### 2.3 关键交互细节

**进度展示**
```typescript
interface ProgressStage {
  id: string;
  name: string;           // "需求解析"
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;       // 0-100
  detail?: string;        // "正在分析几何约束..."
  subtasks?: ProgressStage[];  // 子任务列表
  startTime?: Date;
  endTime?: Date;
}
```

**错误处理展示**
```typescript
interface ErrorDisplay {
  type: 'validation' | 'geometry' | 'llm' | 'system';
  message: string;
  suggestion: string;     // "尝试简化描述，减少特征数量"
  retryable: boolean;
  fallback?: {           // 降级方案
    available: boolean;
    description: string;
  };
}
```

---

## 3. 复杂需求自动拆分策略

### 3.1 复杂度评估算法

```python
class ComplexityEvaluator:
    """
    评估设计需求的复杂度，决定是否拆分
    """
    
    WEIGHTS = {
        'part_count': 2.0,        # 部件数量权重
        'feature_count': 1.5,     # 特征数量权重
        'boolean_ops': 2.5,       # 布尔运算复杂度
        'dependency_depth': 1.8,  # 依赖深度
        'tolerance_count': 1.2,   # 公差要求数量
        'material_complexity': 0.8, # 材料复杂度
    }
    
    THRESHOLDS = {
        'simple': 10,      # 单任务处理
        'moderate': 25,    # 简单拆分
        'complex': 50,     # 深度拆分
    }
    
    def evaluate(self, parsed_design: DesignIntent) -> ComplexityScore:
        score = 0
        factors = []
        
        # 1. 部件数量分析
        if parsed_design.has_multiple_parts():
            score += len(parsed_design.parts) * self.WEIGHTS['part_count']
            factors.append(f"多部件设计: {len(parsed_design.parts)} 个")
        
        # 2. 特征数量分析
        feature_count = len(parsed_design.features)
        if feature_count > 5:
            score += feature_count * self.WEIGHTS['feature_count']
            factors.append(f"特征数量: {feature_count}")
        
        # 3. 布尔运算复杂度
        boolean_complexity = self._analyze_boolean_ops(parsed_design)
        score += boolean_complexity * self.WEIGHTS['boolean_ops']
        
        # 4. 依赖关系深度
        dependency_depth = self._calculate_dependency_depth(parsed_design)
        score += dependency_depth * self.WEIGHTS['dependency_depth']
        
        return ComplexityScore(
            total_score=score,
            level=self._categorize(score),
            factors=factors,
            should_decompose=score > self.THRESHOLDS['simple']
        )
```

### 3.2 拆分策略

```python
class TaskDecomposer:
    """
    将复杂设计拆分为可管理的子任务
    """
    
    def decompose(self, design: DesignIntent) -> List[SubTask]:
        """
        拆分策略选择
        """
        strategy = self._select_strategy(design)
        
        if strategy == 'by_part':
            return self._split_by_parts(design)
        elif strategy == 'by_feature':
            return self._split_by_features(design)
        elif strategy == 'by_operation':
            return self._split_by_operations(design)
        elif strategy == 'hierarchical':
            return self._hierarchical_split(design)
    
    def _split_by_parts(self, design: DesignIntent) -> List[SubTask]:
        """
        按部件拆分 - 适用于多零件装配
        """
        subtasks = []
        for i, part in enumerate(design.parts):
            subtasks.append(SubTask(
                id=f"part_{i}",
                name=f"生成部件: {part.name}",
                type='part_generation',
                dependencies=[],  # 部件间可能无依赖
                design_intent=part,
                estimated_complexity=self.evaluator.evaluate(part),
                merge_strategy='assembly'  # 最终装配
            ))
        return subtasks
    
    def _split_by_features(self, design: DesignIntent) -> List[SubTask]:
        """
        按特征拆分 - 适用于单零件多特征
        """
        # 按特征依赖关系拓扑排序
        sorted_features = self._topological_sort(design.features)
        
        subtasks = []
        current_batch = []
        current_complexity = 0
        
        for feature in sorted_features:
            feature_complexity = self._estimate_feature_complexity(feature)
            
            # 如果当前批次太复杂，创建新任务
            if current_complexity + feature_complexity > 15 and current_batch:
                subtasks.append(self._create_feature_task(current_batch, subtasks))
                current_batch = []
                current_complexity = 0
            
            current_batch.append(feature)
            current_complexity += feature_complexity
        
        # 添加最后一批
        if current_batch:
            subtasks.append(self._create_feature_task(current_batch, subtasks))
        
        return subtasks
    
    def _hierarchical_split(self, design: DesignIntent) -> List[SubTask]:
        """
        层级拆分 - 复杂装配体的多层次拆分
        """
        subtasks = []
        
        # Level 1: 主体结构
        subtasks.append(SubTask(
            id="main_body",
            name="生成主体结构",
            type='base_geometry',
            dependencies=[],
            priority=1
        ))
        
        # Level 2: 主要特征
        for i, major_feature in enumerate(design.major_features):
            subtasks.append(SubTask(
                id=f"feature_{i}",
                name=f"添加{major_feature.name}",
                type='feature_addition',
                dependencies=["main_body"],
                priority=2
            ))
        
        # Level 3: 细节特征
        for i, detail in enumerate(design.details):
            parent_id = self._find_parent_feature(detail)
            subtasks.append(SubTask(
                id=f"detail_{i}",
                name=f"添加{detail.name}",
                type='detail_addition',
                dependencies=[parent_id],
                priority=3
            ))
        
        return subtasks
```

### 3.3 依赖关系图

```python
class DependencyGraph:
    """
    管理子任务间的依赖关系
    """
    
    def build(self, subtasks: List[SubTask]) -> Dict[str, List[str]]:
        """
        构建依赖图
        """
        graph = {task.id: [] for task in subtasks}
        
        for task in subtasks:
            for dep_id in task.dependencies:
                if dep_id in graph:
                    graph[dep_id].append(task.id)
        
        return graph
    
    def get_execution_order(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """
        获取并行执行层级
        """
        # 拓扑排序，返回可并行执行的批次
        in_degree = {node: 0 for node in graph}
        for node, deps in graph.items():
            for dep in deps:
                in_degree[dep] += 1
        
        levels = []
        while in_degree:
            # 找出入度为0的节点（无依赖）
            current_level = [node for node, deg in in_degree.items() if deg == 0]
            
            if not current_level:
                raise ValueError("循环依赖 detected")
            
            levels.append(current_level)
            
            # 移除当前层，更新入度
            for node in current_level:
                del in_degree[node]
                for neighbor in graph[node]:
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
        
        return levels
```

---

## 4. CAD JSON Schema 设计

### 4.1 核心 Schema 结构

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "text-to-cad-schema-v1",
  "title": "Text-to-CAD Modeling Plan",
  "type": "object",
  "required": ["version", "metadata", "coordinate_system", "steps"],
  "properties": {
    "version": {
      "type": "string",
      "enum": ["1.0"],
      "description": "Schema版本"
    },
    "metadata": {
      "type": "object",
      "required": ["design_name", "author", "created_at"],
      "properties": {
        "design_name": { "type": "string" },
        "description": { "type": "string" },
        "author": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "units": {
          "type": "string",
          "enum": ["mm", "cm", "m", "inch"],
          "default": "mm"
        },
        "tolerance": {
          "type": "number",
          "default": 0.01,
          "description": "默认公差"
        }
      }
    },
    "coordinate_system": {
      "type": "object",
      "description": "全局坐标系定义",
      "properties": {
        "origin": {
          "type": "array",
          "items": { "type": "number" },
          "minItems": 3,
          "maxItems": 3,
          "default": [0, 0, 0]
        },
        "x_axis": { "$ref": "#/definitions/vector3" },
        "y_axis": { "$ref": "#/definitions/vector3" },
        "z_axis": { "$ref": "#/definitions/vector3" }
      }
    },
    "parameters": {
      "type": "object",
      "description": "全局参数定义",
      "patternProperties": {
        "^[a-zA-Z_][a-zA-Z0-9_]*$": {
          "type": "object",
          "properties": {
            "value": { "type": "number" },
            "description": { "type": "string" },
            "constraints": {
              "type": "object",
              "properties": {
                "min": { "type": "number" },
                "max": { "type": "number" }
              }
            }
          }
        }
      }
    },
    "steps": {
      "type": "array",
      "description": "建模步骤序列",
      "items": { "$ref": "#/definitions/modeling_step" },
      "minItems": 1
    }
  },
  
  "definitions": {
    "vector3": {
      "type": "array",
      "items": { "type": "number" },
      "minItems": 3,
      "maxItems": 3
    },
    
    "point2d": {
      "type": "array",
      "items": { "type": "number" },
      "minItems": 2,
      "maxItems": 2
    },
    
    "point3d": {
      "type": "array",
      "items": { "type": "number" },
      "minItems": 3,
      "maxItems": 3
    },
    
    "modeling_step": {
      "oneOf": [
        { "$ref": "#/definitions/sketch_step" },
        { "$ref": "#/definitions/extrude_step" },
        { "$ref": "#/definitions/cut_step" },
        { "$ref": "#/definitions/hole_step" },
        { "$ref": "#/definitions/fillet_step" },
        { "$ref": "#/definitions/chamfer_step" },
        { "$ref": "#/definitions/boolean_step" },
        { "$ref": "#/definitions/transform_step" },
        { "$ref": "#/definitions/loft_step" },
        { "$ref": "#/definitions/revolve_step" }
      ]
    },
    
    "sketch_step": {
      "type": "object",
      "required": ["type", "id", "plane", "entities"],
      "properties": {
        "type": { "const": "sketch" },
        "id": { "type": "string" },
        "plane": {
          "oneOf": [
            { "enum": ["XY", "YZ", "XZ", "front", "top", "right"] },
            { "$ref": "#/definitions/plane_definition" }
          ]
        },
        "entities": {
          "type": "array",
          "items": { "$ref": "#/definitions/sketch_entity" }
        },
        "constraints": {
          "type": "array",
          "items": { "$ref": "#/definitions/constraint" }
        }
      }
    },
    
    "sketch_entity": {
      "oneOf": [
        { "$ref": "#/definitions/line_entity" },
        { "$ref": "#/definitions/circle_entity" },
        { "$ref": "#/definitions/rectangle_entity" },
        { "$ref": "#/definitions/arc_entity" },
        { "$ref": "#/definitions/polygon_entity" },
        { "$ref": "#/definitions/spline_entity" }
      ]
    },
    
    "line_entity": {
      "type": "object",
      "required": ["type", "start", "end"],
      "properties": {
        "type": { "const": "line" },
        "id": { "type": "string" },
        "start": { "$ref": "#/definitions/point2d" },
        "end": { "$ref": "#/definitions/point2d" },
        "construction": { "type": "boolean", "default": false }
      }
    },
    
    "circle_entity": {
      "type": "object",
      "required": ["type", "center", "radius"],
      "properties": {
        "type": { "const": "circle" },
        "id": { "type": "string" },
        "center": { "$ref": "#/definitions/point2d" },
        "radius": { 
          "oneOf": [
            { "type": "number" },
            { "type": "string", "pattern": "^\\$[a-zA-Z_][a-zA-Z0-9_]*$" }
          ]
        },
        "construction": { "type": "boolean", "default": false }
      }
    },
    
    "rectangle_entity": {
      "type": "object",
      "required": ["type", "origin", "width", "height"],
      "properties": {
        "type": { "const": "rectangle" },
        "id": { "type": "string" },
        "origin": { "$ref": "#/definitions/point2d" },
        "width": { 
          "oneOf": [
            { "type": "number" },
            { "type": "string", "pattern": "^\\$[a-zA-Z_][a-zA-Z0-9_]*$" }
          ]
        },
        "height": { 
          "oneOf": [
            { "type": "number" },
            { "type": "string", "pattern": "^\\$[a-zA-Z_][a-zA-Z0-9_]*$" }
          ]
        },
        "angle": { "type": "number", "default": 0 },
        "centered": { "type": "boolean", "default": false }
      }
    },
    
    "extrude_step": {
      "type": "object",
      "required": ["type", "sketch_id", "distance"],
      "properties": {
        "type": { "const": "extrude" },
        "sketch_id": { "type": "string" },
        "distance": { 
          "oneOf": [
            { "type": "number" },
            { "type": "string", "pattern": "^\\$[a-zA-Z_][a-zA-Z0-9_]*$" }
          ]
        },
        "direction": {
          "type": "string",
          "enum": ["positive", "negative", "both"],
          "default": "positive"
        },
        "operation": {
          "type": "string",
          "enum": ["new", "add", "cut", "intersect"],
          "default": "new"
        },
        "taper_angle": { "type": "number", "default": 0 }
      }
    },
    
    "cut_step": {
      "type": "object",
      "required": ["type", "sketch_id", "distance"],
      "properties": {
        "type": { "const": "cut" },
        "sketch_id": { "type": "string" },
        "distance": { "type": "number" },
        "through_all": { "type": "boolean", "default": false },
        "direction": {
          "type": "string",
          "enum": ["positive", "negative", "both"],
          "default": "positive"
        }
      }
    },
    
    "hole_step": {
      "type": "object",
      "required": ["type", "position", "diameter"],
      "properties": {
        "type": { "const": "hole" },
        "position": { "$ref": "#/definitions/point3d" },
        "diameter": { "type": "number" },
        "depth": { "type": "number" },
        "through_all": { "type": "boolean", "default": false },
        "counterbore": {
          "type": "object",
          "properties": {
            "diameter": { "type": "number" },
            "depth": { "type": "number" }
          }
        },
        "countersink": {
          "type": "object",
          "properties": {
            "diameter": { "type": "number" },
            "angle": { "type": "number" }
          }
        }
      }
    },
    
    "fillet_step": {
      "type": "object",
      "required": ["type", "edges", "radius"],
      "properties": {
        "type": { "const": "fillet" },
        "edges": {
          "type": "array",
          "items": { "type": "string" },
          "description": "边引用ID列表"
        },
        "radius": { "type": "number" }
      }
    },
    
    "chamfer_step": {
      "type": "object",
      "required": ["type", "edges", "distance"],
      "properties": {
        "type": { "const": "chamfer" },
        "edges": {
          "type": "array",
          "items": { "type": "string" }
        },
        "distance": { "type": "number" },
        "distance2": { "type": "number" },
        "angle": { "type": "number" }
      }
    },
    
    "boolean_step": {
      "type": "object",
      "required": ["type", "operation", "target", "tool"],
      "properties": {
        "type": { "const": "boolean" },
        "operation": {
          "type": "string",
          "enum": ["union", "subtract", "intersect"]
        },
        "target": { "type": "string", "description": "目标实体ID" },
        "tool": { "type": "string", "description": "工具实体ID" },
        "keep_tool": { "type": "boolean", "default": false }
      }
    },
    
    "transform_step": {
      "type": "object",
      "required": ["type", "target", "transform"],
      "properties": {
        "type": { "const": "transform" },
        "target": { "type": "string" },
        "transform": {
          "type": "object",
          "properties": {
            "translate": { "$ref": "#/definitions/vector3" },
            "rotate": {
              "type": "object",
              "properties": {
                "axis": { "$ref": "#/definitions/vector3" },
                "angle": { "type": "number" }
              }
            },
            "scale": { "$ref": "#/definitions/vector3" },
            "mirror": {
              "type": "object",
              "properties": {
                "plane": { "$ref": "#/definitions/plane_definition" }
              }
            }
          }
        }
      }
    },
    
    "plane_definition": {
      "type": "object",
      "required": ["origin", "normal"],
      "properties": {
        "origin": { "$ref": "#/definitions/point3d" },
        "normal": { "$ref": "#/definitions/vector3" },
        "x_direction": { "$ref": "#/definitions/vector3" }
      }
    },
    
    "constraint": {
      "type": "object",
      "required": ["type", "entities"],
      "properties": {
        "type": {
          "enum": ["coincident", "parallel", "perpendicular", "horizontal", 
                   "vertical", "equal", "tangent", "concentric", "distance", 
                   "angle", "radius", "diameter", "fix"]
        },
        "entities": {
          "type": "array",
          "items": { "type": "string" }
        },
        "value": { "type": "number" }
      }
    }
  }
}
```

### 4.2 示例 JSON

```json
{
  "version": "1.0",
  "metadata": {
    "design_name": "铝合金安装支架",
    "description": "用于固定设备的L型支架",
    "author": "AutoCAD-LLM",
    "created_at": "2026-03-08T10:30:00Z",
    "units": "mm",
    "tolerance": 0.01
  },
  "coordinate_system": {
    "origin": [0, 0, 0],
    "x_axis": [1, 0, 0],
    "y_axis": [0, 1, 0],
    "z_axis": [0, 0, 1]
  },
  "parameters": {
    "base_width": {
      "value": 100,
      "description": "底板宽度",
      "constraints": { "min": 10, "max": 500 }
    },
    "base_depth": {
      "value": 80,
      "description": "底板深度"
    },
    "thickness": {
      "value": 5,
      "description": "板材厚度"
    },
    "hole_diameter": {
      "value": 6.5,
      "description": "螺栓孔直径"
    }
  },
  "steps": [
    {
      "type": "sketch",
      "id": "base_profile",
      "plane": "XY",
      "entities": [
        {
          "type": "rectangle",
          "id": "rect1",
          "origin": [0, 0],
          "width": "$base_width",
          "height": "$base_depth",
          "centered": true
        },
        {
          "type": "circle",
          "id": "hole1",
          "center": [-35, -25],
          "radius": "$hole_diameter / 2"
        },
        {
          "type": "circle",
          "id": "hole2",
          "center": [35, -25],
          "radius": "$hole_diameter / 2"
        },
        {
          "type": "circle",
          "id": "hole3",
          "center": [-35, 25],
          "radius": "$hole_diameter / 2"
        },
        {
          "type": "circle",
          "id": "hole4",
          "center": [35, 25],
          "radius": "$hole_diameter / 2"
        }
      ]
    },
    {
      "type": "extrude",
      "sketch_id": "base_profile",
      "distance": "$thickness",
      "direction": "positive",
      "operation": "new"
    },
    {
      "type": "fillet",
      "edges": ["edge_1", "edge_2", "edge_3", "edge_4"],
      "radius": 2
    }
  ]
}
```

---

## 5. LLM 建模规划策略

### 5.1 提示词工程框架

```python
SYSTEM_PROMPT = """
你是一个专业的 CAD 建模工程师，擅长将自然语言描述转换为精确的参数化 CAD 建模计划。

你的任务是：
1. 理解用户的机械设计需求
2. 分析几何约束和尺寸关系
3. 规划合理的建模步骤顺序
4. 生成严格符合 JSON Schema 的建模计划

规则：
- 所有尺寸必须明确，不能模糊（如"大约"、"左右"等词不允许出现）
- 优先使用参数化设计，将关键尺寸定义为参数
- 建模步骤必须符合几何依赖关系（先创建基础，再添加特征）
- 复杂设计必须拆分为多个简单步骤，不能试图一次性完成
- 如果需求不明确，使用合理的工程默认值并标注

单位：默认使用毫米(mm)，除非用户明确要求其他单位
坐标系：默认使用右手坐标系，XY平面为基准平面，Z轴向上

输出格式：必须输出合法的 JSON，符合 text-to-cad-schema-v1
"""

USER_PROMPT_TEMPLATE = """
请为以下机械设计需求生成 CAD 建模计划：

设计描述：
{user_description}

要求：
1. 分析设计需求，识别所有几何特征
2. 确定合理的建模顺序
3. 生成参数化的 JSON 建模计划
4. 确保所有尺寸明确且可执行

请只输出 JSON 格式的建模计划，不要输出其他解释文字。
"""

COMPLEXITY_DETECTION_PROMPT = """
分析以下设计需求的复杂度，判断是否需要拆分：

设计描述：{user_description}

判断标准：
- 简单：单一零件，少于5个特征，无复杂布尔运算
- 中等：单一零件，5-10个特征，或有简单布尔运算
- 复杂：多零件装配，或超过10个特征，或有复杂依赖关系

输出格式：
{{
  "complexity": "simple|moderate|complex",
  "should_decompose": true|false,
  "reason": "判断理由",
  "suggested_parts": ["如果复杂，建议拆分为这些部件"]
}}
"""
```

### 5.2 约束策略

```python
class LLMConstraints:
    """
    约束 LLM 输出的策略
    """
    
    STRUCTURED_OUTPUT_SCHEMA = {
        "type": "json_object",
        "schema": CAD_SCHEMA  # 使用 Pydantic 模型定义
    }
    
    CONSTRAINTS = [
        # 1. 几何约束
        "所有草图必须是闭合的",
        "拉伸距离必须为正数",
        "圆角半径必须小于相邻边长度",
        
        # 2. 参数约束
        "参数引用必须使用 $parameter_name 格式",
        "所有参数必须在 parameters 部分定义",
        "参数值必须在合理工程范围内",
        
        # 3. 依赖约束
        "引用的 sketch_id 必须在之前的步骤中定义",
        "布尔运算的目标和工具实体必须存在",
        "特征添加必须基于已存在的实体",
        
        # 4. 顺序约束
        "必须先创建基础几何体，再添加特征",
        "切除操作必须在实体创建之后",
        "圆角/倒角应在主要特征完成后添加",
    ]
    
    @staticmethod
    def validate_step_order(steps: List[Dict]) -> List[str]:
        """
        验证步骤顺序是否合理
        """
        errors = []
        defined_ids = set()
        
        for i, step in enumerate(steps):
            # 检查引用的 sketch_id 是否已定义
            if 'sketch_id' in step:
                if step['sketch_id'] not in defined_ids:
                    errors.append(f"步骤{i}: 引用了未定义的草图 {step['sketch_id']}")
            
            # 记录当前步骤定义的 ID
            if 'id' in step:
                defined_ids.add(step['id'])
        
        return errors
```

### 5.3 自我修正循环

```python
class SelfRefinementLoop:
    """
    LLM 自我修正机制
    """
    
    MAX_ITERATIONS = 3
    
    def generate_with_refinement(self, user_prompt: str) -> Dict:
        """
        带自我修正的生成
        """
        for iteration in range(self.MAX_ITERATIONS):
            # 1. 生成初始方案
            json_plan = self.llm.generate(
                system=SYSTEM_PROMPT,
                user=user_prompt,
                response_format={"type": "json_object"}
            )
            
            # 2. 验证
            validation_result = self.validator.validate(json_plan)
            
            if validation_result.is_valid:
                return json_plan
            
            # 3. 如果验证失败，让 LLM 自我修正
            correction_prompt = f"""
你生成的 CAD 建模计划存在以下问题：

{validation_result.format_errors()}

请修正这些问题，重新生成符合要求的 JSON 建模计划。

原始方案：
{json.dumps(json_plan, indent=2)}

注意：
- 修复所有验证错误
- 保持设计的完整性
- 确保输出仍是合法的 JSON
"""
            
            user_prompt = correction_prompt
        
        # 如果多次尝试仍失败，抛出异常或返回部分结果
        raise GenerationError(f"无法在 {self.MAX_ITERATIONS} 次迭代内生成有效方案")
```

---

## 6. CAD 几何执行引擎选型

### 6.1 方案对比

| 特性 | CadQuery | OpenCascade (PythonOCC) | FreeCAD | build123d |
|------|----------|-------------------------|---------|-----------|
| **内核** | OpenCascade | OpenCascade | OpenCascade | OpenCascade |
| **API 复杂度** | ⭐⭐ 简洁 | ⭐⭐⭐⭐ 复杂 | ⭐⭐⭐ 中等 | ⭐⭐ 简洁 |
| **STEP 导出** | ✅ 原生支持 | ✅ 原生支持 | ✅ 原生支持 | ✅ 原生支持 |
| **参数化** | ✅ 优秀 | ✅ 优秀 | ✅ 优秀 | ✅ 优秀 |
| **Python 集成** | ✅ 优秀 | ✅ 良好 | ⚠️ 需嵌入 | ✅ 优秀 |
| **文档完善度** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **社区活跃度** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **几何稳定性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Web 集成** | ⚠️ 需后端 | ⚠️ 需后端 | ❌ 困难 | ⚠️ 需后端 |

### 6.2 推荐方案：CadQuery

**选择理由：**

1. **简洁的 Python API** - 适合 LLM 生成代码
2. **完整的 STEP 支持** - 原生导入导出
3. **良好的文档** - 降低学习成本
4. **活跃社区** - 有问题可快速解决
5. **几何稳定性** - 基于 OpenCascade 内核

**代码示例：**

```python
import cadquery as cq

# 从 JSON 生成 CAD 模型
def execute_json_plan(json_plan: dict) -> cq.Workplane:
    """
    执行 JSON 建模计划
    """
    workplane = None
    
    for step in json_plan['steps']:
        step_type = step['type']
        
        if step_type == 'sketch':
            # 创建草图
            wp = cq.Workplane(step.get('plane', 'XY'))
            
            for entity in step['entities']:
                if entity['type'] == 'rectangle':
                    width = resolve_parameter(entity['width'], json_plan['parameters'])
                    height = resolve_parameter(entity['height'], json_plan['parameters'])
                    wp = wp.rect(width, height)
                
                elif entity['type'] == 'circle':
                    radius = resolve_parameter(entity['radius'], json_plan['parameters'])
                    center = entity['center']
                    wp = wp.moveTo(center[0], center[1]).circle(radius)
            
            workplane = wp
        
        elif step_type == 'extrude':
            distance = resolve_parameter(step['distance'], json_plan['parameters'])
            operation = step.get('operation', 'new')
            
            if operation == 'new':
                result = workplane.extrude(distance)
            elif operation == 'add':
                result = result.union(workplane.extrude(distance))
            elif operation == 'cut':
                result = result.cut(workplane.extrude(distance))
            
            workplane = result
        
        elif step_type == 'hole':
            position = step['position']
            diameter = step['diameter']
            depth = step.get('depth')
            
            hole_wp = cq.Workplane("XY").moveTo(position[0], position[1])
            
            if step.get('through_all'):
                result = result.faces(">Z").workplane().hole(diameter)
            else:
                result = result.faces(">Z").workplane().hole(diameter, depth)
            
            workplane = result
        
        elif step_type == 'fillet':
            radius = step['radius']
            # 对所有边应用圆角
            result = workplane.edges().fillet(radius)
            workplane = result
    
    return workplane

def export_step(model: cq.Workplane, filepath: str):
    """
    导出 STEP 文件
    """
    model.val().exportStep(filepath)
```

### 6.3 备选方案：PythonOCC

如果需要更底层的控制，可以使用 PythonOCC：

```python
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.Interface import Interface_Static

# 更底层的控制，但代码更复杂
```

---

## 7. 3D 模型预览方案

### 7.1 技术方案

由于浏览器无法直接渲染 STEP 文件，需要转换：

```
STEP → (CadQuery) → STL/OBJ → (three.js) → glTF → WebGL 渲染
```

**推荐方案：**

1. **后端转换**：CadQuery → mesh → STL/glTF
2. **前端渲染**：React Three Fiber + drei

### 7.2 后端转换

```python
import cadquery as cq
import meshio

def convert_step_to_gltf(step_path: str, output_path: str):
    """
    将 STEP 转换为 glTF 用于网页预览
    """
    # 1. 读取 STEP
    shape = cq.importers.importStep(step_path)
    
    # 2. 转换为网格
    mesh = shape.val().toTriangles(0.1)  # 0.1mm 容差
    
    # 3. 导出为 glTF
    meshio.write(output_path, mesh, file_format="glTF")
    
    return output_path

def convert_step_to_stl(step_path: str, output_path: str, tolerance: float = 0.1):
    """
    将 STEP 转换为 STL
    """
    shape = cq.importers.importStep(step_path)
    shape.val().exportStl(output_path, tolerance=tolerance)
    return output_path
```

### 7.3 前端渲染

```typescript
// React Three Fiber 组件
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF, Grid } from '@react-three/drei'

function ModelViewer({ modelUrl }: { modelUrl: string }) {
  const { scene } = useGLTF(modelUrl)
  
  return (
    <Canvas camera={{ position: [100, 100, 100], fov: 50 }}>
      {/* 环境光 */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      
      {/* 网格地面 */}
      <Grid
        args={[200, 200]}
        cellSize={10}
        cellThickness={0.5}
        cellColor="#6f6f6f"
        sectionSize={50}
        sectionThickness={1}
        sectionColor="#9d4b4b"
      />
      
      {/* 3D 模型 */}
      <primitive object={scene} scale={1} />
      
      {/* 控制器 */}
      <OrbitControls 
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
      />
    </Canvas>
  )
}

// 加载状态
function ModelLoader({ taskId }: { taskId: string }) {
  const [modelUrl, setModelUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // 轮询获取预览模型
    const checkModel = async () => {
      const response = await fetch(`/api/tasks/${taskId}/preview`)
      if (response.ok) {
        const blob = await response.blob()
        setModelUrl(URL.createObjectURL(blob))
        setLoading(false)
      }
    }
    
    const interval = setInterval(checkModel, 2000)
    return () => clearInterval(interval)
  }, [taskId])
  
  if (loading) return <div>加载模型中...</div>
  if (!modelUrl) return <div>模型生成失败</div>
  
  return <ModelViewer modelUrl={modelUrl} />
}
```

### 7.4 性能优化

```typescript
// 使用 useMemo 缓存几何体
const cachedGeometry = useMemo(() => {
  return geometry.clone()
}, [geometry])

// 渐进式加载
function ProgressiveModel({ url }: { url: string }) {
  const { scene, progress } = useGLTF(url, true) // true = 渐进式加载
  
  return (
    <>
      {progress < 100 && (
        <Html center>
          <div>加载进度: {progress.toFixed(0)}%</div>
        </Html>
      )}
      <primitive object={scene} />
    </>
  )
}
```

---

## 8. 进度展示与任务状态系统

### 8.1 状态机设计

```python
from enum import Enum, auto

class TaskStatus(Enum):
    # 初始状态
    PENDING = "pending"
    
    # 需求解析阶段
    PARSING_REQUIREMENTS = "parsing_requirements"
    REQUIREMENTS_PARSED = "requirements_parsed"
    
    # 复杂度评估阶段
    EVALUATING_COMPLEXITY = "evaluating_complexity"
    COMPLEXITY_EVALUATED = "complexity_evaluated"
    
    # 任务拆分阶段
    DECOMPOSING_TASK = "decomposing_task"
    TASK_DECOMPOSED = "task_decomposed"
    
    # LLM 生成阶段
    GENERATING_PLAN = "generating_plan"
    PLAN_GENERATED = "plan_generated"
    
    # 验证阶段
    VALIDATING_JSON = "validating_json"
    JSON_VALIDATED = "json_validated"
    
    # CAD 执行阶段
    EXECUTING_CAD = "executing_cad"
    CAD_EXECUTED = "cad_executed"
    
    # 导出阶段
    EXPORTING_STEP = "exporting_step"
    STEP_EXPORTED = "step_exported"
    
    # 预览生成阶段
    GENERATING_PREVIEW = "generating_preview"
    PREVIEW_GENERATED = "preview_generated"
    
    # 完成/失败
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStateMachine:
    """
    任务状态机
    """
    
    TRANSITIONS = {
        TaskStatus.PENDING: [
            TaskStatus.PARSING_REQUIREMENTS,
            TaskStatus.FAILED
        ],
        TaskStatus.PARSING_REQUIREMENTS: [
            TaskStatus.REQUIREMENTS_PARSED,
            TaskStatus.FAILED
        ],
        TaskStatus.REQUIREMENTS_PARSED: [
            TaskStatus.EVALUATING_COMPLEXITY,
            TaskStatus.FAILED
        ],
        TaskStatus.EVALUATING_COMPLEXITY: [
            TaskStatus.COMPLEXITY_EVALUATED,
            TaskStatus.FAILED
        ],
        TaskStatus.COMPLEXITY_EVALUATED: [
            TaskStatus.DECOMPOSING_TASK,
            TaskStatus.GENERATING_PLAN,  # 简单任务跳过拆分
            TaskStatus.FAILED
        ],
        TaskStatus.DECOMPOSING_TASK: [
            TaskStatus.TASK_DECOMPOSED,
            TaskStatus.FAILED
        ],
        TaskStatus.TASK_DECOMPOSED: [
            TaskStatus.GENERATING_PLAN,
            TaskStatus.FAILED
        ],
        TaskStatus.GENERATING_PLAN: [
            TaskStatus.PLAN_GENERATED,
            TaskStatus.FAILED
        ],
        TaskStatus.PLAN_GENERATED: [
            TaskStatus.VALIDATING_JSON,
            TaskStatus.FAILED
        ],
        TaskStatus.VALIDATING_JSON: [
            TaskStatus.JSON_VALIDATED,
            TaskStatus.GENERATING_PLAN,  # 验证失败，重试
            TaskStatus.FAILED
        ],
        TaskStatus.JSON_VALIDATED: [
            TaskStatus.EXECUTING_CAD,
            TaskStatus.FAILED
        ],
        TaskStatus.EXECUTING_CAD: [
            TaskStatus.CAD_EXECUTED,
            TaskStatus.FAILED
        ],
        TaskStatus.CAD_EXECUTED: [
            TaskStatus.EXPORTING_STEP,
            TaskStatus.FAILED
        ],
        TaskStatus.EXPORTING_STEP: [
            TaskStatus.STEP_EXPORTED,
            TaskStatus.FAILED
        ],
        TaskStatus.STEP_EXPORTED: [
            TaskStatus.GENERATING_PREVIEW,
            TaskStatus.COMPLETED  # 可以跳过预览
        ],
        TaskStatus.GENERATING_PREVIEW: [
            TaskStatus.PREVIEW_GENERATED,
            TaskStatus.COMPLETED  # 预览失败但仍可完成
        ],
        TaskStatus.PREVIEW_GENERATED: [
            TaskStatus.COMPLETED
        ],
    }
    
    def can_transition(self, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        return to_status in self.TRANSITIONS.get(from_status, [])
```

### 8.2 实时通知

```python
# WebSocket 实时通知
from fastapi import WebSocket

class TaskNotifier:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[task_id] = websocket
    
    async def notify_progress(self, task_id: str, progress: TaskProgress):
        if task_id in self.connections:
            await self.connections[task_id].send_json({
                "type": "progress",
                "data": progress.to_dict()
            })
    
    async def notify_complete(self, task_id: str, result: TaskResult):
        if task_id in self.connections:
            await self.connections[task_id].send_json({
                "type": "complete",
                "data": result.to_dict()
            })
        # 完成后关闭连接
        await self.connections[task_id].close()
        del self.connections[task_id]
```

---

## 9. 项目代码结构设计

```
text-to-cad/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── frontend/                          # React 前端
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── public/
│   │   └── favicon.ico
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── DesignInput/         # 设计输入组件
│       │   ├── ProgressPanel/       # 进度面板
│       │   ├── ModelViewer/         # 3D模型预览
│       │   ├── TaskHistory/         # 历史任务
│       │   └── common/              # 通用组件
│       ├── hooks/
│       │   ├── useTask.ts           # 任务管理Hook
│       │   ├── useWebSocket.ts      # WebSocket Hook
│       │   └── useModelViewer.ts    # 3D预览Hook
│       ├── services/
│       │   ├── api.ts               # API客户端
│       │   └── websocket.ts         # WebSocket服务
│       ├── stores/
│       │   └── taskStore.ts         # 状态管理(Zustand/Redux)
│       ├── types/
│       │   └── index.ts             # TypeScript类型定义
│       └── styles/
│           └── global.css
│
├── backend/                           # FastAPI 后端
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic/                       # 数据库迁移
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI入口
│   │   ├── config.py                  # 配置管理
│   │   ├── database.py                # 数据库连接
│   │   │
│   │   ├── api/                       # API路由
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tasks.py           # 任务API
│   │   │   │   ├── models.py          # 模型文件API
│   │   │   │   └── websocket.py       # WebSocket端点
│   │   │   └── deps.py                # 依赖注入
│   │   │
│   │   ├── core/                      # 核心业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── task_orchestrator.py   # 任务编排器
│   │   │   ├── complexity_evaluator.py # 复杂度评估
│   │   │   └── task_decomposer.py     # 任务拆分器
│   │   │
│   │   ├── llm/                       # LLM相关
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # LLM客户端
│   │   │   ├── prompts.py             # 提示词模板
│   │   │   ├── planner.py             # 建模规划器
│   │   │   └── refinement.py          # 自我修正
│   │   │
│   │   ├── cad/                       # CAD执行
│   │   │   ├── __init__.py
│   │   │   ├── executor.py            # CAD执行器
│   │   │   ├── exporter.py            # STEP导出
│   │   │   └── preview_generator.py   # 预览生成
│   │   │
│   │   ├── schema/                    # Schema定义
│   │   │   ├── __init__.py
│   │   │   ├── cad_schema.json        # JSON Schema文件
│   │   │   ├── validator.py           # Schema验证器
│   │   │   └── models.py              # Pydantic模型
│   │   │
│   │   ├── models/                    # 数据库模型
│   │   │   ├── __init__.py
│   │   │   ├── task.py                # 任务模型
│   │   │   └── user.py                # 用户模型
│   │   │
│   │   └── services/                  # 服务层
│   │       ├── __init__.py
│   │       ├── storage.py             # 文件存储服务
│   │       └── notification.py        # 通知服务
│   │
│   └── tests/                         # 测试
│       ├── unit/
│       └── integration/
│
├── worker/                            # Celery 任务队列
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── celery_app.py                  # Celery应用
│   └── tasks/
│       ├── __init__.py
│       ├── cad_tasks.py               # CAD任务
│       └── llm_tasks.py               # LLM任务
│
├── shared/                            # 共享代码
│   ├── __init__.py
│   ├── schemas/                       # 共享Schema
│   │   ├── __init__.py
│   │   ├── task.py
│   │   └── cad.py
│   └── utils/
│       ├── __init__.py
│       └── validators.py
│
└── infrastructure/                    # 基础设施
    ├── docker/
    │   ├── Dockerfile.frontend
    │   ├── Dockerfile.backend
    │   └── Dockerfile.worker
    ├── k8s/                           # Kubernetes配置
    └── scripts/
        ├── setup.sh
        └── deploy.sh
```

---

## 10. 错误检测与自动修复机制

### 10.1 错误分类

```python
class CADErrorType(Enum):
    # 几何错误
    NON_MANIFOLD = "non_manifold"           # 非流形几何
    INVALID_BOOLEAN = "invalid_boolean"     # 布尔运算失败
    SELF_INTERSECTING = "self_intersecting" # 自相交
    
    # 约束错误
    UNCLOSED_SKETCH = "unclosed_sketch"     # 草图未闭合
    DIMENSION_CONFLICT = "dimension_conflict" # 尺寸冲突
    MISSING_CONSTRAINT = "missing_constraint" # 缺少约束
    
    # 结构错误
    INVALID_DEPENDENCY = "invalid_dependency" # 依赖错误
    CIRCULAR_REFERENCE = "circular_reference" # 循环引用
    
    # LLM错误
    HALLUCINATION = "hallucination"         # 几何幻觉
    INVALID_SCHEMA = "invalid_schema"       # Schema不符合
    
    # 系统错误
    TIMEOUT = "timeout"                     # 超时
    MEMORY_ERROR = "memory_error"           # 内存不足
    EXPORT_FAILED = "export_failed"         # 导出失败

class CADError(Exception):
    def __init__(
        self,
        error_type: CADErrorType,
        message: str,
        step_id: Optional[str] = None,
        recoverable: bool = True,
        suggestion: Optional[str] = None
    ):
        self.error_type = error_type
        self.step_id = step_id
        self.recoverable = recoverable
        self.suggestion = suggestion
        super().__init__(message)
```

### 10.2 自动修复策略

```python
class AutoRepairEngine:
    """
    自动修复常见CAD错误
    """
    
    def repair(self, error: CADError, json_plan: Dict) -> RepairResult:
        """
        尝试自动修复错误
        """
        repair_handlers = {
            CADErrorType.UNCLOSED_SKETCH: self._repair_unclosed_sketch,
            CADErrorType.DIMENSION_CONFLICT: self._repair_dimension_conflict,
            CADErrorType.NON_MANIFOLD: self._repair_non_manifold,
            CADErrorType.INVALID_BOOLEAN: self._repair_boolean,
            CADErrorType.HALLUCINATION: self._repair_hallucination,
        }
        
        handler = repair_handlers.get(error.error_type)
        if handler:
            return handler(error, json_plan)
        
        return RepairResult(
            success=False,
            message=f"无法自动修复: {error.error_type.value}"
        )
    
    def _repair_unclosed_sketch(self, error: CADError, json_plan: Dict) -> RepairResult:
        """
        修复未闭合草图
        """
        step_id = error.step_id
        step = self._find_step(json_plan, step_id)
        
        if not step or step['type'] != 'sketch':
            return RepairResult(success=False, message="找不到草图步骤")
        
        # 尝试自动闭合草图
        entities = step.get('entities', [])
        
        # 1. 检查是否有明显的间隙
        # 2. 尝试添加线段闭合
        # 3. 或者添加约束使其闭合
        
        # 简化的修复：添加一个close标志
        step['auto_close'] = True
        
        return RepairResult(
            success=True,
            message="已启用自动闭合",
            modified_plan=json_plan
        )
    
    def _repair_dimension_conflict(self, error: CADError, json_plan: Dict) -> RepairResult:
        """
        修复尺寸冲突
        """
        # 调整相互冲突的尺寸
        # 例如：如果两个孔距离太近，增加间距
        
        return RepairResult(
            success=True,
            message="已调整冲突尺寸",
            modified_plan=json_plan
        )
    
    def _repair_hallucination(self, error: CADError, json_plan: Dict) -> RepairResult:
        """
        修复 LLM 幻觉
        """
        # 1. 识别不合理的几何
        # 2. 使用合理的默认值替换
        # 3. 或者让 LLM 重新生成这一部分
        
        return RepairResult(
            success=False,  # 幻觉通常需要 LLM 重新生成
            message="几何不合理，需要重新生成",
            requires_llm_regeneration=True
        )
```

---

## 11. 完整示例流程

### 11.1 用户输入

```
创建一个铝合金安装支架，底部是100x80mm的矩形板，厚度5mm，
四角有M6螺栓孔（距离边缘各10mm），中心有一个直径30mm的圆孔。
整体高度15mm，两侧有高度10mm的加强筋。
```

### 11.2 系统处理流程

```
1. [0s] 用户提交需求
   └─ 状态: PENDING → PARSING_REQUIREMENTS
   └─ 显示: "正在解析需求..."

2. [0.5s] 需求解析完成
   └─ 识别特征: 底板、螺栓孔x4、中心孔、加强筋x2
   └─ 状态: PARSING_REQUIREMENTS → REQUIREMENTS_PARSED
   └─ 显示: "✅ 需求解析完成，识别到 7 个特征"

3. [1s] 复杂度评估
   └─ 评估结果: 中等复杂度，无需拆分
   └─ 状态: REQUIREMENTS_PARSED → EVALUATING_COMPLEXITY → COMPLEXITY_EVALUATED
   └─ 显示: "✅ 复杂度评估: 中等（单一零件）"

4. [1.5s] LLM 生成建模计划
   └─ 生成 JSON: 包含 5 个步骤
   └─ 状态: COMPLEXITY_EVALUATED → GENERATING_PLAN → PLAN_GENERATED
   └─ 显示: "⏳ 正在生成建模计划 (3/5)..."

5. [3s] JSON 验证
   └─ 验证通过
   └─ 状态: PLAN_GENERATED → VALIDATING_JSON → JSON_VALIDATED
   └─ 显示: "✅ JSON验证通过"

6. [3.5s] 执行 CAD 建模
   └─ 步骤1: 创建底板草图
   └─ 步骤2: 拉伸底板
   └─ 步骤3: 创建螺栓孔
   └─ 步骤4: 创建中心孔
   └─ 步骤5: 添加加强筋
   └─ 状态: JSON_VALIDATED → EXECUTING_CAD → CAD_EXECUTED
   └─ 显示: "⏳ 正在执行CAD建模 (4/5)..."

7. [5s] 导出 STEP
   └─ 生成文件: bracket_20260308_105030.step
   └─ 状态: CAD_EXECUTED → EXPORTING_STEP → STEP_EXPORTED
   └─ 显示: "✅ STEP导出完成"

8. [6s] 生成预览
   └─ 转换为 glTF
   └─ 状态: STEP_EXPORTED → GENERATING_PREVIEW → PREVIEW_GENERATED
   └─ 显示: "⏳ 正在生成预览模型..."

9. [8s] 完成
   └─ 状态: PREVIEW_GENERATED → COMPLETED
   └─ 显示: 
      ✅ 设计完成！
      📊 体积: 128.5 cm³
      📐 尺寸: 100×80×15 mm
      [查看3D模型] [下载STEP] [查看JSON方案]
```

---

## 12. 项目实现路线图

### Phase 1: MVP (4-6 周)

**目标**: 基础功能可用，支持简单零件

**任务清单**:
- [ ] 基础项目搭建 (FastAPI + React + PostgreSQL)
- [ ] 简单 Prompt → CadQuery 代码生成
- [ ] 基础 STEP 导出
- [ ] 简单 3D 预览 (STL 格式)
- [ ] 任务状态跟踪
- [ ] 用户界面基础功能

**技术栈**:
- 后端: Python 3.11 + FastAPI + Celery
- 前端: React 18 + TypeScript + Three.js
- CAD: CadQuery
- 数据库: PostgreSQL + Redis
- LLM: Claude 3.5 Sonnet / GPT-4

### Phase 2: 增强功能 (4-6 周)

**目标**: 支持复杂设计，提升稳定性

**任务清单**:
- [ ] JSON Schema 完整实现
- [ ] 复杂度评估 + 任务拆分
- [ ] Schema 验证器
- [ ] 自动修复机制
- [ ] 参数化设计支持
- [ ] glTF 预览优化
- [ ] 错误处理完善

### Phase 3: 工程级功能 (6-8 周)

**目标**: 生产就绪，支持工业应用

**任务清单**:
- [ ] 多用户支持 + 认证
- [ ] 历史版本管理
- [ ] 设计模板库
- [ ] 高级约束支持
- [ ] 装配体支持
- [ ] 性能优化
- [ ] API 文档完善
- [ ] 部署 + CI/CD

### 推荐开发语言 & 框架

| 层级 | 推荐方案 | 理由 |
|------|----------|------|
| **后端** | Python 3.11 + FastAPI | CadQuery 集成、高性能、现代 |
| **前端** | React 18 + TypeScript | 生态丰富、类型安全 |
| **3D 渲染** | React Three Fiber | React 集成、声明式 API |
| **CAD 引擎** | CadQuery | Pythonic、OpenCascade 内核 |
| **任务队列** | Celery + Redis | 成熟、Python 原生 |
| **数据库** | PostgreSQL | 关系型、JSON 支持 |
| **文件存储** | MinIO | S3 兼容、自托管 |
| **LLM** | Claude 3.5 Sonnet / GPT-4 | 强代码生成能力 |
| **容器化** | Docker + Docker Compose | 开发部署一致 |

### 快速启动命令

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/text-to-cad.git
cd text-to-cad

# 2. 启动基础设施
docker-compose up -d postgres redis minio

# 3. 安装后端依赖
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 运行后端
uvicorn app.main:app --reload

# 5. 安装前端依赖 (新终端)
cd frontend
npm install

# 6. 运行前端
npm run dev

# 7. 启动 Celery Worker (新终端)
cd backend
celery -A worker.celery_app worker --loglevel=info
```

---

## 附录: 参考资源

### 相关论文
1. "Text-to-CadQuery: A New Paradigm for CAD Generation with Scalable Large Model Capabilities" (2025)
2. "STEP-LLM: Generating CAD STEP Models from Natural Language with Large Language Models" (2026)
3. "CAD-CODER: An Open-Source Vision-Language Model for Computer-Aided Design Code"

### 开源项目
- CadQuery: https://github.com/CadQuery/cadquery
- React Three Fiber: https://github.com/pmndrs/react-three-fiber
- three-cad-viewer: https://github.com/bernhard-42/three-cad-viewer

### 文档
- CadQuery 文档: https://cadquery.readthedocs.io/
- OpenCascade 文档: https://dev.opencascade.org/doc/
- STEP 标准: https://www.steptools.com/stds/step/

---

*文档版本: 1.0*
*最后更新: 2026-03-08*
