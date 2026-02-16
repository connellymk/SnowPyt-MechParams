"""
Example: Creating Multiple Slabs from Pits with Multiple Test Results

This example demonstrates how to use the create_slabs() method to create
multiple slabs from a single pit when there are multiple ECT or CT test results.
"""

from snowpyt_mechparams.snowpilot import parse_caaml_directory
from snowpyt_mechparams.data_structures import Pit
import pandas as pd


def process_pits_with_multiple_slabs(caaml_directory):
    """
    Process all pits in a directory and create slabs for each ECTP result.

    Returns a DataFrame with one row per slab, including metadata about
    which test result was used to create each slab.
    """
    # Parse all CAAML files in the directory
    profiles = parse_caaml_directory(caaml_directory)

    # Store slab data
    slab_data = []

    for pit_idx, profile in enumerate(profiles):
        # Create Pit object
        pit = Pit.from_snowpylot_profile(profile)

        # Create slabs for all ECTP results
        slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

        # Extract data from each slab
        for slab in slabs:
            # Use pit_id if available, otherwise assign a sequential ID
            effective_pit_id = slab.pit_id if slab.pit_id else f"pit_{pit_idx:05d}"

            slab_info = {
                'pit_id': effective_pit_id,
                'slab_id': slab.slab_id,
                'weak_layer_source': slab.weak_layer_source,
                'test_result_index': slab.test_result_index,
                'n_test_results_in_pit': slab.n_test_results_in_pit,
                'weak_layer_depth': slab.weak_layer.depth_top if slab.weak_layer else None,
                'n_layers': len(slab.layers),
                'slab_thickness': slab.total_thickness,
                'slope_angle': slab.angle,
                # Test properties
                'test_score': slab.test_result_properties.get('score') if slab.test_result_properties else None,
                'test_propagation': slab.test_result_properties.get('propagation') if slab.test_result_properties else None,
                'test_depth': slab.test_result_properties.get('depth_top') if slab.test_result_properties else None,
            }
            slab_data.append(slab_info)

    # Convert to DataFrame
    df = pd.DataFrame(slab_data)
    return df


def summarize_slabs_per_pit(df):
    """Summarize the distribution of slabs per pit."""
    slabs_per_pit = df.groupby('pit_id').size()

    print("\nSlabs per Pit Distribution:")
    print(f"Total pits: {len(slabs_per_pit)}")
    print(f"Total slabs: {len(df)}")
    print(f"\nDistribution:")
    for n_slabs, count in slabs_per_pit.value_counts().sort_index().items():
        print(f"  {count} pits with {n_slabs} slab(s)")

    return slabs_per_pit


def compare_parameter_across_slabs(df, parameter='D11'):
    """
    Example: Compare a mechanical parameter across slabs.

    This function demonstrates how you might analyze parameter values
    across all slabs, accounting for multiple slabs per pit.
    """
    # Group by pit to see variation within pits
    within_pit_variation = df.groupby('pit_id')[parameter].agg(['mean', 'std', 'count'])

    # Filter to pits with multiple slabs
    multiple_slabs = within_pit_variation[within_pit_variation['count'] > 1]

    print(f"\nWithin-Pit Variation of {parameter}:")
    print(f"Pits with multiple slabs: {len(multiple_slabs)}")
    if len(multiple_slabs) > 0:
        print(f"Average std dev within pits: {multiple_slabs['std'].mean():.3f}")

    return within_pit_variation


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python multiple_slabs_example.py <path_to_caaml_directory>")
        sys.exit(1)

    caaml_dir = sys.argv[1]

    print(f"Processing pits from: {caaml_dir}")

    # Process all pits and create slabs
    df = process_pits_with_multiple_slabs(caaml_dir)

    # Save to CSV
    output_file = "slab_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved slab data to: {output_file}")

    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    summarize_slabs_per_pit(df)

    # Print sample of the data
    print("\n" + "="*60)
    print("SAMPLE DATA (first 10 slabs)")
    print("="*60)
    print(df.head(10).to_string())

    # Note about statistical analysis
    print("\n" + "="*60)
    print("IMPORTANT: Statistical Considerations")
    print("="*60)
    print("""
When analyzing mechanical parameters (like D11) across slabs:

1. MULTIPLE SLABS PER PIT ARE NOT INDEPENDENT
   - Slabs from the same pit share layer data
   - They are spatially correlated
   - Standard statistical tests assume independence

2. RECOMMENDED APPROACHES:
   - Use mixed-effects models with pit_id as random effect
   - Use clustered standard errors
   - Conduct sensitivity analyses (e.g., one slab per pit)

3. REPORTING:
   - Always report: total pits, total slabs, slabs-per-pit distribution
   - Calculate ICC (intraclass correlation) to quantify within-pit correlation
   - Present results from multiple statistical approaches

See the project README for more details on handling non-independent slabs.
""")
