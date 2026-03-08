"""
Mock CAD Executor for testing without full CadQuery installation
"""

from typing import Dict, Optional, Union
from app.schema.models import (
    CADModelPlan, SketchStep, ExtrudeStep, HoleStep, FilletStep,
    resolve_parameter
)


class MockWorkplane:
    """Mock CadQuery Workplane for testing"""
    
    def __init__(self, name="MockWorkplane"):
        self.name = name
        self.operations = []
    
    def rect(self, width, height, centered=True):
        self.operations.append(f"rect({width}, {height}, centered={centered})")
        return self
    
    def circle(self, radius):
        self.operations.append(f"circle({radius})")
        return self
    
    def moveTo(self, x, y):
        self.operations.append(f"moveTo({x}, {y})")
        return self
    
    def extrude(self, distance):
        self.operations.append(f"extrude({distance})")
        return self
    
    def union(self, other):
        self.operations.append(f"union({other})")
        return self
    
    def cut(self, other):
        self.operations.append(f"cut({other})")
        return self
    
    def edges(self):
        return self
    
    def fillet(self, radius):
        self.operations.append(f"fillet({radius})")
        return self
    
    def val(self):
        return MockShape()
    
    def __repr__(self):
        return f"MockWorkplane({self.operations})"


class MockShape:
    """Mock shape for testing"""
    
    def Volume(self):
        return 12345.67  # Mock volume in cubic mm
    
    def BoundingBox(self):
        class MockBBox:
            xlen = 100.0
            ylen = 80.0
            zlen = 5.0
            xmin = -50.0
            ymin = -40.0
            zmin = 0.0
            xmax = 50.0
            ymax = 40.0
            zmax = 5.0
        return MockBBox()
    
    def exportStep(self, filepath):
        # Create a mock STEP file
        with open(filepath, 'w') as f:
            f.write("ISO-10303-21;\n")
            f.write("HEADER;\n")
            f.write("FILE_DESCRIPTION(('Mock STEP'), '2;1');\n")
            f.write("FILE_NAME('mock.step', '2026-03-08', ('Test'), (''), '', '', '');\n")
            f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 3 1 1 }'));\n")
            f.write("ENDSEC;\n")
            f.write("DATA;\n")
            f.write("#1 = CARTESIAN_POINT('Origin', (0.0, 0.0, 0.0));\n")
            f.write("ENDSEC;\n")
            f.write("END-ISO-10303-21;\n")
    
    def exportStl(self, filepath, tolerance=0.1):
        # Create a mock STL file
        with open(filepath, 'wb') as f:
            # Minimal binary STL header
            f.write(b'\x00' * 80)  # Header
            f.write((1).to_bytes(4, 'little'))  # Number of triangles
            # One triangle
            f.write(b'\x00' * 12)  # Normal
            f.write(b'\x00' * 12)  # Vertex 1
            f.write(b'\x00' * 12)  # Vertex 2
            f.write(b'\x00' * 12)  # Vertex 3
            f.write(b'\x00\x00')  # Attribute


class CADExecutionError(Exception):
    """Error during CAD execution"""
    pass


class CADExecutor:
    """
    Mock CAD Executor for testing
    Uses mock objects when CadQuery is not available
    """
    
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance
        self.workplane: Optional[MockWorkplane] = None
        self.sketches: Dict[str, MockWorkplane] = {}
    
    def execute_plan(self, plan: CADModelPlan):
        """
        Execute a complete CAD modeling plan (mock version)
        """
        self.workplane = None
        self.sketches = {}
        
        parameters = plan.parameters or {}
        
        for step in plan.steps:
            try:
                if isinstance(step, SketchStep):
                    self._execute_sketch(step, parameters)
                elif isinstance(step, ExtrudeStep):
                    self._execute_extrude(step, parameters)
                elif isinstance(step, HoleStep):
                    self._execute_hole(step, parameters)
                elif isinstance(step, FilletStep):
                    self._execute_fillet(step, parameters)
                else:
                    raise CADExecutionError(f"Unknown step type: {type(step)}")
            except Exception as e:
                raise CADExecutionError(
                    f"Error executing step '{step.type}': {str(e)}"
                ) from e
        
        if self.workplane is None:
            raise CADExecutionError("No geometry was generated")
        
        return self.workplane
    
    def _execute_sketch(self, step: SketchStep, parameters: Dict):
        """Execute a sketch step"""
        wp = MockWorkplane(f"sketch_{step.id}")
        
        from app.schema.models import RectangleEntity, CircleEntity
        
        for entity in step.entities:
            if isinstance(entity, RectangleEntity):
                width = resolve_parameter(entity.width, parameters)
                height = resolve_parameter(entity.height, parameters)
                wp = wp.rect(width, height, entity.centered)
            elif isinstance(entity, CircleEntity):
                center = entity.center
                radius = resolve_parameter(entity.radius, parameters)
                wp = wp.moveTo(center[0], center[1]).circle(radius)
        
        self.sketches[step.id] = wp
    
    def _execute_extrude(self, step: ExtrudeStep, parameters: Dict):
        """Execute an extrude step"""
        if step.sketch_id not in self.sketches:
            raise CADExecutionError(f"Sketch '{step.sketch_id}' not found")
        
        sketch = self.sketches[step.sketch_id]
        distance = resolve_parameter(step.distance, parameters)
        
        extruded = sketch.extrude(distance)
        
        if step.operation == "new":
            self.workplane = extruded
        elif step.operation == "add":
            if self.workplane is None:
                raise CADExecutionError("Cannot add: no existing geometry")
            self.workplane = self.workplane.union(extruded)
        elif step.operation == "cut":
            if self.workplane is None:
                raise CADExecutionError("Cannot cut: no existing geometry")
            self.workplane = self.workplane.cut(extruded)
    
    def _execute_hole(self, step: HoleStep, parameters: Dict):
        """Execute a hole step"""
        if self.workplane is None:
            raise CADExecutionError("Cannot create hole: no existing geometry")
        
        diameter = resolve_parameter(step.diameter, parameters)
        hole = MockWorkplane("hole").circle(diameter / 2).extrude(-10)
        self.workplane = self.workplane.cut(hole)
    
    def _execute_fillet(self, step: FilletStep, parameters: Dict):
        """Execute a fillet step"""
        if self.workplane is None:
            raise CADExecutionError("Cannot apply fillet: no existing geometry")
        
        self.workplane = self.workplane.edges().fillet(step.radius)
    
    def export_step(self, filepath: str) -> str:
        """Export STEP file"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.workplane.val().exportStep(filepath)
        return filepath
    
    def export_stl(self, filepath: str, tolerance: float = 0.1) -> str:
        """Export STL file"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.workplane.val().exportStl(filepath, tolerance)
        return filepath
    
    def get_volume(self) -> float:
        """Get volume"""
        if self.workplane is None:
            return 0.0
        return self.workplane.val().Volume()
    
    def get_bounding_box(self) -> Dict[str, float]:
        """Get bounding box"""
        if self.workplane is None:
            return {"x": 0, "y": 0, "z": 0}
        
        bbox = self.workplane.val().BoundingBox()
        return {
            "x": bbox.xlen,
            "y": bbox.ylen,
            "z": bbox.zlen,
            "xmin": bbox.xmin,
            "ymin": bbox.ymin,
            "zmin": bbox.zmin,
            "xmax": bbox.xmax,
            "ymax": bbox.ymax,
            "zmax": bbox.zmax
        }
