"""
Tests for the parameterization algorithm.

This module tests the algorithm for finding calculation pathways from
snow_pit to target parameters, including both layer-level and slab-level
parameters.
"""

import pytest

from snowpyt_mechparams.algorithm import (
    PathSegment,
    Branch,
    Parameterization,
    find_parameterizations,
)
from snowpyt_mechparams.graph import graph


class TestPathSegment:
    """Test PathSegment data structure."""
    
    def test_create_path_segment(self):
        """Should be able to create a path segment."""
        seg = PathSegment(
            from_node="density",
            edge_name="bergfeld",
            to_node="elastic_modulus"
        )
        assert seg.from_node == "density"
        assert seg.edge_name == "bergfeld"
        assert seg.to_node == "elastic_modulus"
    
    def test_path_segment_str(self):
        """Path segment string representation should be readable."""
        seg = PathSegment("a", "method", "b")
        assert str(seg) == "a -- method --> b"


class TestBranch:
    """Test Branch data structure."""
    
    def test_create_branch(self):
        """Should be able to create a branch."""
        segments = [
            PathSegment("snow_pit", "data_flow", "measured_density"),
            PathSegment("measured_density", "data_flow", "density"),
        ]
        branch = Branch(segments=segments)
        assert len(branch.segments) == 2
    
    def test_branch_str(self):
        """Branch string representation should show full path."""
        segments = [
            PathSegment("a", "edge1", "b"),
            PathSegment("b", "edge2", "c"),
        ]
        branch = Branch(segments=segments)
        assert str(branch) == "a -- edge1 --> b -- edge2 --> c"
    
    def test_empty_branch_str(self):
        """Empty branch should have special representation."""
        branch = Branch(segments=[])
        assert str(branch) == "(empty branch)"


class TestParameterization:
    """Test Parameterization data structure."""
    
    def test_create_parameterization(self):
        """Should be able to create a parameterization."""
        branch = Branch(segments=[
            PathSegment("snow_pit", "data_flow", "measured_density")
        ])
        param = Parameterization(branches=[branch], merge_points=[])
        assert len(param.branches) == 1
        assert len(param.merge_points) == 0


class TestFindParameterizationsLayerLevel:
    """Test finding parameterizations for layer-level parameters."""
    
    def test_find_density_parameterizations(self):
        """Should find all density calculation pathways."""
        node = graph.get_node("density")
        pathways = find_parameterizations(graph, node)
        
        # Should have: 1 data_flow + 3 calculation methods
        # geldsetzer, kim_jamieson_table2, kim_jamieson_table5
        assert len(pathways) == 4
        
        # Check that we have expected methods
        # Methods can be in segments or in merge point continuations
        methods_used = []
        for pathway in pathways:
            # Check branch segments
            for branch in pathway.branches:
                for seg in branch.segments:
                    if seg.to_node == "density":
                        methods_used.append(seg.edge_name)
            # Check merge point continuations
            for _, _, continuation in pathway.merge_points:
                for seg in continuation:
                    if seg.to_node == "density":
                        methods_used.append(seg.edge_name)
        
        assert "data_flow" in methods_used
        assert "geldsetzer" in methods_used
        assert "kim_jamieson_table2" in methods_used
        assert "kim_jamieson_table5" in methods_used
    
    def test_find_elastic_modulus_parameterizations(self):
        """Should find all elastic modulus calculation pathways."""
        node = graph.get_node("elastic_modulus")
        pathways = find_parameterizations(graph, node)
        
        # Should have: 4 density methods × 4 E methods = 16 pathways
        assert len(pathways) == 16
        
        # Check that all pathways end with elastic_modulus
        for pathway in pathways:
            # Check merge points
            if pathway.merge_points:
                last_merge = pathway.merge_points[-1]
                continuation = last_merge[2]
                if continuation:
                    assert continuation[-1].to_node == "elastic_modulus"
    
    def test_find_poissons_ratio_parameterizations(self):
        """Should find all Poisson's ratio calculation pathways."""
        node = graph.get_node("poissons_ratio")
        pathways = find_parameterizations(graph, node)
        
        # kochle (grain_form only) + srivastava (density + grain_form)
        # srivastava has 4 density methods → 1 + 4 = 5 pathways
        assert len(pathways) == 5
    
    def test_find_shear_modulus_parameterizations(self):
        """Should find all shear modulus calculation pathways."""
        node = graph.get_node("shear_modulus")
        pathways = find_parameterizations(graph, node)
        
        # wautier method with 4 density methods
        assert len(pathways) == 4


class TestFindParameterizationsSlabLevel:
    """Test finding parameterizations for slab-level parameters."""
    
    def test_find_A11_parameterizations(self):
        """Should find all A11 calculation pathways."""
        node = graph.get_node("A11")
        pathways = find_parameterizations(graph, node)
        
        # A11 requires: thickness + E + ν
        # - layer_thickness: 1 pathway
        # - E: 4 density methods × 4 E methods = 16 pathways
        # - ν: 1 kochle + 4 srivastava (with density) = 5 pathways
        # Total: 16 (E) × 5 (ν) × 1 (thickness) = 80 pathways
        assert len(pathways) == 80
        
        # Check that all pathways use weissgraeber_rosendahl
        for pathway in pathways:
            has_method = False
            # Check in merge points continuation
            for _, _, continuation in pathway.merge_points:
                for seg in continuation:
                    if seg.to_node == "A11":
                        assert seg.edge_name == "weissgraeber_rosendahl"
                        has_method = True
            assert has_method, "A11 pathway missing weissgraeber_rosendahl"
    
    def test_find_B11_parameterizations(self):
        """Should find all B11 calculation pathways."""
        node = graph.get_node("B11")
        pathways = find_parameterizations(graph, node)
        
        # B11 requires: thickness + E + ν (same as A11)
        # Total: 16 (E) × 5 (ν) × 1 (thickness) = 80 pathways
        assert len(pathways) == 80
    
    def test_find_D11_parameterizations(self):
        """Should find all D11 calculation pathways."""
        node = graph.get_node("D11")
        pathways = find_parameterizations(graph, node)
        
        # D11 requires: zi (thickness) + E + ν
        # Total: 16 (E) × 5 (ν) × 1 (thickness) = 80 pathways
        assert len(pathways) == 80
        
        # Verify structure includes merge nodes
        for pathway in pathways:
            # Should have multiple branches merging
            assert len(pathway.branches) >= 2
            # Should have merge points
            assert len(pathway.merge_points) >= 1
    
    def test_find_A55_parameterizations(self):
        """Should find all A55 calculation pathways."""
        node = graph.get_node("A55")
        pathways = find_parameterizations(graph, node)
        
        # A55 requires: thickness + G
        # Only wautier method for G with 4 density methods
        # = 4 pathways
        assert len(pathways) == 4


class TestParameterizationStructure:
    """Test the structure of parameterizations."""
    
    def test_simple_parameterization_has_one_branch(self):
        """Simple pathways should have one branch."""
        # Poisson's ratio from kochle (grain_form only)
        node = graph.get_node("poissons_ratio")
        pathways = find_parameterizations(graph, node)
        
        # Find the kochle pathway (no density needed)
        kochle_pathways = [
            p for p in pathways
            if any(
                seg.edge_name == "kochle" and seg.to_node == "poissons_ratio"
                for branch in p.branches
                for seg in branch.segments
            )
        ]
        
        assert len(kochle_pathways) == 1
        pathway = kochle_pathways[0]
        
        # Should have one branch
        assert len(pathway.branches) == 1
        # Should have no merge points (simple linear path)
        assert len(pathway.merge_points) == 0
    
    def test_merged_parameterization_has_multiple_branches(self):
        """Pathways with merges should have multiple branches."""
        # Elastic modulus requires density + grain_form merge
        node = graph.get_node("elastic_modulus")
        pathways = find_parameterizations(graph, node)
        
        # All should have multiple branches (density path + grain_form path)
        for pathway in pathways:
            assert len(pathway.branches) >= 2
            assert len(pathway.merge_points) >= 1
    
    def test_slab_parameterization_has_complex_structure(self):
        """Slab parameterizations should have complex structure."""
        node = graph.get_node("D11")
        pathways = find_parameterizations(graph, node)
        
        # Take first pathway and verify structure
        pathway = pathways[0]
        
        # Should have multiple branches
        assert len(pathway.branches) >= 3  # At least thickness, E, ν paths
        
        # Should have multiple merge points
        assert len(pathway.merge_points) >= 2  # At least merge_E_nu and merge_zi_E_nu
        
        # Final merge should lead to D11
        final_merge = pathway.merge_points[-1]
        continuation = final_merge[2]
        if continuation:
            assert continuation[-1].to_node == "D11"


class TestPathwayCount:
    """Test that pathway counts match expected combinatorics."""
    
    def test_pathway_count_formula(self):
        """Pathway count should match product of alternative methods."""
        # For elastic_modulus:
        # - 4 ways to get density (data_flow, geldsetzer, KJ_t2, KJ_t5)
        # - 1 way to get grain_form (data_flow)
        # - 4 ways to calculate E (bergfeld, kochle, wautier, schottner)
        # Total: 4 × 1 × 4 = 16
        
        E_node = graph.get_node("elastic_modulus")
        pathways = find_parameterizations(graph, E_node)
        assert len(pathways) == 16
    
    def test_slab_pathway_count_formula(self):
        """Slab pathway count should match layer parameter combinations."""
        # For D11:
        # - layer_thickness: 1 pathway (data_flow)
        # - E (elastic_modulus): 4 density × 4 E methods = 16 pathways
        # - ν (poissons_ratio): kochle (1) + srivastava with 4 density = 5 pathways
        # 
        # These combine via merge nodes:
        # - merge_E_nu combines all E and ν pathways: 16 × 5 = 80 combinations
        # - zi uses layer_thickness: 1 pathway
        # - merge_zi_E_nu combines zi with merge_E_nu: 1 × 80 = 80
        # 
        # Total: 80 pathways
        
        D11_node = graph.get_node("D11")
        pathways = find_parameterizations(graph, D11_node)
        assert len(pathways) == 80


class TestGraphIntegration:
    """Test integration between algorithm and graph."""
    
    def test_all_layer_parameters_have_pathways(self):
        """All layer parameters should have at least one pathway."""
        layer_params = ["density", "elastic_modulus", "poissons_ratio", "shear_modulus"]
        
        for param in layer_params:
            node = graph.get_node(param)
            pathways = find_parameterizations(graph, node)
            assert len(pathways) > 0, f"{param} has no pathways"
    
    def test_all_slab_parameters_have_pathways(self):
        """All slab parameters should have at least one pathway."""
        slab_params = ["A11", "B11", "D11", "A55"]
        
        for param in slab_params:
            node = graph.get_node(param)
            pathways = find_parameterizations(graph, node)
            assert len(pathways) > 0, f"{param} has no pathways"
    
    def test_pathways_start_from_snow_pit(self):
        """All pathways should start from snow_pit."""
        node = graph.get_node("elastic_modulus")
        pathways = find_parameterizations(graph, node)
        
        for pathway in pathways:
            # Every branch should start from snow_pit
            for branch in pathway.branches:
                if branch.segments:
                    assert branch.segments[0].from_node == "snow_pit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
