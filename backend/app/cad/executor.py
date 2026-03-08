"""
CAD Executor using CadQuery
Converts JSON modeling plans to actual 3D geometry
"""

import cadquery as cq
import os
from typing import Dict, Optional, Union
from app.schema.models import (
    CADModelPlan, SketchStep, ExtrudeStep, HoleStep, FilletStep,
    resolve_parameter, RectangleEntity, CircleEntity
)


class CADExecutionError(Exception):
    """Error during CAD execution"""
    pass


class CADExecutor:
    """
    Executes CAD modeling plans using CadQuery
    """
    
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance
        self.workplane: Optional[cq.Workplane] = None
        self.sketches: Dict[str, cq.Workplane] = {}
    
    def execute_plan(self, plan: CADModelPlan) -> cq.Workplane:
        """
        Execute a complete CAD modeling plan
        
        Args:
            plan: The CAD modeling plan
            
        Returns:
            Final CadQuery Workplane with the completed model
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
    
    def _execute_sketch(
        self, 
        step: SketchStep, 
        parameters: Dict
    ) -> None:
        """Execute a sketch step"""
        # Determine the plane
        if isinstance(step.plane, str):
            plane_name = step.plane
        else:
            # Custom plane not yet implemented
            plane_name = "XY"
        
        # Create workplane on the specified plane
        wp = cq.Workplane(plane_name)
        
        # Build the sketch with all entities
        for entity in step.entities:
            wp = self._add_entity(wp, entity, parameters)
        
        # Store the sketch for later reference
        self.sketches[step.id] = wp
    
    def _add_entity(
        self, 
        wp: cq.Workplane, 
        entity: Union[RectangleEntity, CircleEntity],
        parameters: Dict
    ) -> cq.Workplane:
        """Add a sketch entity to the workplane"""
        if isinstance(entity, RectangleEntity):
            width = resolve_parameter(entity.width, parameters)
            height = resolve_parameter(entity.height, parameters)
            
            if entity.centered:
                wp = wp.rect(width, height)
            else:
                # For non-centered, we need to adjust
                wp = wp.rect(width, height, centered=False)
        
        elif isinstance(entity, CircleEntity):
            center = entity.center
            radius = resolve_parameter(entity.radius, parameters)
            
            # Move to center position and draw circle
            wp = wp.moveTo(center[0], center[1]).circle(radius)
        
        return wp
    
    def _execute_extrude(
        self, 
        step: ExtrudeStep, 
        parameters: Dict
    ) -> None:
        """Execute an extrude step"""
        if step.sketch_id not in self.sketches:
            raise CADExecutionError(f"Sketch '{step.sketch_id}' not found")
        
        sketch = self.sketches[step.sketch_id]
        distance = resolve_parameter(step.distance, parameters)
        
        # Perform extrusion
        extruded = sketch.extrude(distance)
        
        # Apply operation
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
    
    def _execute_hole(
        self, 
        step: HoleStep, 
        parameters: Dict
    ) -> None:
        """Execute a hole step"""
        if self.workplane is None:
            raise CADExecutionError("Cannot create hole: no existing geometry")
        
        diameter = resolve_parameter(step.diameter, parameters)
        radius = diameter / 2
        position = step.position
        
        # Create a cylinder for the hole
        if step.through_all:
            # Get the bounding box to determine depth
            bbox = self.workplane.val().BoundingBox()
            depth = max(bbox.xlen, bbox.ylen, bbox.zlen) * 2
        else:
            depth = step.depth if step.depth else 10.0
        
        # Create hole cylinder
        hole = (cq.Workplane("XY")
                .moveTo(position[0], position[1])
                .circle(radius)
                .extrude(-depth))  # Negative for downward
        
        # Cut the hole
        self.workplane = self.workplane.cut(hole)
    
    def _execute_fillet(
        self, 
        step: FilletStep, 
        parameters: Dict
    ) -> None:
        """Execute a fillet step"""
        if self.workplane is None:
            raise CADExecutionError("Cannot apply fillet: no existing geometry")
        
        if step.edges == "all":
            # Apply fillet to all edges
            self.workplane = self.workplane.edges().fillet(step.radius)
        else:
            # Specific edges not yet implemented
            raise CADExecutionError("Specific edge selection not yet implemented")
    
    def export_step(self, filepath: str) -> str:
        """
        Export the current model to STEP format
        
        Args:
            filepath: Output file path
            
        Returns:
            Path to the exported file
        """
        if self.workplane is None:
            raise CADExecutionError("No model to export")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Export STEP
        self.workplane.val().exportStep(filepath)
        
        return filepath
    
    def export_stl(self, filepath: str, tolerance: float = 0.1) -> str:
        """
        Export the current model to STL format (for preview)
        
        Args:
            filepath: Output file path
            tolerance: Mesh tolerance
            
        Returns:
            Path to the exported file
        """
        if self.workplane is None:
            raise CADExecutionError("No model to export")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Export STL with specified tolerance
        self.workplane.val().exportStl(filepath, tolerance=tolerance)
        
        return filepath
    
    def get_volume(self) -> float:
        """Get the volume of the current model in cubic mm"""
        if self.workplane is None:
            return 0.0
        return self.workplane.val().Volume()
    
    def get_bounding_box(self) -> Dict[str, float]:
        """Get the bounding box dimensions"""
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
