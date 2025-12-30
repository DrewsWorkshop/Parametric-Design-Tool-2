import json
from collections import Counter
import random
import os

def encode(x, xl, xu, m):
    """Encode parameter value to binary string"""
    scaled_x = int(((x - xl) / (xu - xl)) * (2**m - 1))
    return format(scaled_x, f'0{m}b')

def get_config_ranges(object_type):
    """Get parameter ranges - same for all object types"""
    return [
        ("Segment Count", (2, 9), 5),
        ("Object Width", (1.5, 4.0), 3.0),
        ("Twist Angle", (0, 45), 20),
        ("Twist Groove Depth", (0, 5), 1),
        ("Vertical Wave Frequency", (0, 20), 3),
        ("Vertical Wave Depth", (0, 5), 1),
    ]

def mutate(binary_str, mutationProb=0.1):
    mutated = list(binary_str)  # Convert string to list for mutability

    for i in range(len(mutated)):
        if random.uniform(0, 1) <= mutationProb:
            mutated[i] = '1' if mutated[i] == '0' else '0'  # Flip the bit

    return ''.join(mutated)  # Convert back to string

def decode(binary_str, xl, xu, m):
    int_val = int(binary_str, 2)
    return xl + (int_val / (2**m - 1)) * (xu - xl)

def decode_design(binary_str, object_type):
    ranges = get_config_ranges(object_type)
    param_names = [name for name, _, _ in ranges]
    decoded_params = {}
    for i, param_name in enumerate(param_names):
        start = i * 6
        end = start + 6
        param_binary = binary_str[start:end]
        _, (xl, xu), _ = ranges[i]
        decoded_value = decode(param_binary, xl, xu, 6)
        decoded_params[param_name] = decoded_value
    return decoded_params

def write_designs_to_file(all_generated_designs, output_file, verbose=True):
    """Write all generated designs to a JSON file"""
    if all_generated_designs:
        # Create tmp directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write designs to file
        with open(output_file, 'w') as f:
            f.write("[\n")
            for i, (object_type, design_params) in enumerate(all_generated_designs):
                f.write("  {\n")
                f.write(f'    "object_type": "{object_type}",\n')
                f.write('    "parameters": {\n')
                param_items = list(design_params.items())
                for j, (param, value) in enumerate(param_items):
                    comma = "," if j < len(param_items) - 1 else ""
                    f.write(f'      "{param}": {value}{comma}\n')
                f.write("    }\n")
                f.write("  }")
                if i < len(all_generated_designs) - 1:
                    f.write(",")
                f.write("\n")
            f.write("]")
        
        if verbose:
            print(f"\nAll designs saved to {output_file}")
        return output_file
    else:
        if verbose:
            print("\nNo designs were generated")
        return None

def crossover(parent1, parent2, crossoverProb=1):
    """Perform single-point crossover between two genetic codes.

    Cut only at parameter boundaries so each 6-bit parameter stays intact.
    Allowed cut positions are between bits: 6/7, 12/13, 24/25.
    This preserves related parameter pairs (3,4) and (5,6).
    """
    if random.uniform(0, 1) <= crossoverProb:
        m = len(parent1)  # Length of genetic code
        # Use ratio-based boundary cuts so logic is resilient to bit-length changes
        # Defaults correspond to boundaries after groups [1-2], [3-4], [5-6] when there are 6 params
        boundary_fracs = (1/6, 2/6, 4/6)
        candidate_positions = {
            max(1, min(m - 1, int(round(m * frac)))) for frac in boundary_fracs
        }
        # Filter to interior unique positions
        allowed_cuts = sorted(p for p in candidate_positions if 1 <= p <= m - 1)
        if not allowed_cuts:
            # Fallback to any interior point if unexpected length
            allowed_cuts = list(range(1, max(1, m - 1)))
        crossPoint = random.choice(allowed_cuts)

        print(f"CrossPoint: {crossPoint}")

        # Perform Single-Point Crossover at boundary
        child1 = parent1[:crossPoint] + parent2[crossPoint:]
        child2 = parent2[:crossPoint] + parent1[crossPoint:]
    else:
        child1 = parent1
        child2 = parent2
    
    return child1, child2

def create_ga_file(all_designs):
    filename = "designsGA.txt"
    with open(filename, 'w') as f:
        f.write("[\n")
        for i, (object_type, design_params) in enumerate(all_designs):
            f.write("  {\n")
            f.write(f'    "object_type": "{object_type}",\n')
            f.write('    "parameters": {\n')
            param_items = list(design_params.items())
            for j, (param, value) in enumerate(param_items):
                comma = "," if j < len(param_items) - 1 else ""
                f.write(f'      "{param}": {value}{comma}\n')
            f.write("    }\n")
            f.write("  }")
            if i < len(all_designs) - 1:
                f.write(",")
            f.write("\n")
        f.write("]")
    return filename

def run_genetic_algorithm(favorites_file="favorites.txt", output_file="tmp/designsGA.txt", verbose=True):
    """
    Run the genetic algorithm to generate new designs from favorites
    
    Args:
        favorites_file (str): Path to the favorites JSON file
        output_file (str): Path for the output designs file
        verbose (bool): Whether to print progress information
    
    Returns:
        str: Path to the generated designs file, or None if no designs generated
    """
    # Read favorites
    with open(favorites_file, 'r') as f:
        data = json.load(f)

    # Count each object type
    object_types = [item['object_type'] for item in data]
    counts = Counter(object_types)

    if verbose:
        print("Object types and amounts:")
        for obj_type, count in counts.items():
            print(f"  {obj_type}: {count}")

    # Encode parameters for each favorite and group by type
    if verbose:
        print("\nEncoded parameters (6-bit binary):")
    genetic_codes_by_type = {}

    for i, item in enumerate(data):
        object_type = item['object_type']
        params = item['parameters']
        ranges = get_config_ranges(object_type)
        
        if ranges is None:
            if verbose:
                print(f"  {object_type} {i+1}: Could not load config")
            continue
            
        encoded_params = []
        for param_name, param_value in params.items():
            # Find the range for this parameter
            for range_name, (xl, xu), _ in ranges:
                if range_name == param_name:
                    encoded = encode(param_value, xl, xu, 6)
                    encoded_params.append(encoded)
                    break
        
        # Concatenate all binary strings into one
        genetic_code = ''.join(encoded_params)
        if verbose:
            print(f"  {object_type} {i+1}: {genetic_code}")
        
        # Group by object type
        if object_type not in genetic_codes_by_type:
            genetic_codes_by_type[object_type] = []
        genetic_codes_by_type[object_type].append(genetic_code)

    # Generate designs based on object count
    if verbose:
        print("\nGenerating designs:")
    all_generated_designs = []

    for object_type, genetic_codes in genetic_codes_by_type.items():
        if len(genetic_codes) == 1:
            if verbose:
                print(f"  {object_type}: 1 object - generating 2 mutated designs")
            original = genetic_codes[0]
            design1 = mutate(original)
            design2 = mutate(original)
            if verbose:
                print(f"    Design 1: {design1}")
                print(f"    Design 2: {design2}")
            
            # Decode the designs back to parameters
            design1_params = decode_design(design1, object_type)
            design2_params = decode_design(design2, object_type)
            
            # Add to all designs
            all_generated_designs.append((object_type, design1_params))
            all_generated_designs.append((object_type, design2_params))
            
        elif len(genetic_codes) == 2:
            if verbose:
                print(f"  {object_type}: 2 objects - generating 2 crossover designs")
            parent1, parent2 = genetic_codes[0], genetic_codes[1]
            child1, child2 = crossover(parent1, parent2)
            if verbose:
                print(f"    Parent 1: {parent1}")
                print(f"    Parent 2: {parent2}")
                print(f"    Child 1:  {child1}")
                print(f"    Child 2:  {child2}")
            design3 = mutate(parent1)
            design4 = mutate(parent2)
            
            # Decode the designs back to parameters
            child1_params = decode_design(child1, object_type)
            child2_params = decode_design(child2, object_type)
            design3_params = decode_design(design3, object_type)
            design4_params = decode_design(design4, object_type)
            
            # Add to all designs
            all_generated_designs.append((object_type, child1_params))
            all_generated_designs.append((object_type, child2_params))
            all_generated_designs.append((object_type, design3_params))
            all_generated_designs.append((object_type, design4_params))
            
        elif len(genetic_codes) > 2:
            if verbose:
                print(f"  {object_type}: {len(genetic_codes)} objects - generating 4 designs with random parents")
            
            # Generate 4 designs with random parent selection
            designs = []
            for i in range(4):
                if random.uniform(0, 1) <= 0.5:  # 50% chance for crossover
                    # Random crossover
                    parents = random.sample(genetic_codes, 2)
                    parent1, parent2 = parents[0], parents[1]
                    child1, child2 = crossover(parent1, parent2)
                    design = child1 if i % 2 == 0 else child2
                    if verbose:
                        print(f"    Design {i+1}: Crossover from random parents")
                else:
                    # Random mutation
                    parent = random.choice(genetic_codes)
                    design = mutate(parent)
                    if verbose:
                        print(f"    Design {i+1}: Mutation from random parent")
                designs.append(design)
            
            # Decode all designs back to parameters
            for design in designs:
                params = decode_design(design, object_type)
                all_generated_designs.append((object_type, params))
            
        else:
            if verbose:
                print(f"  {object_type}: {len(genetic_codes)} objects - no design generation")

    # Create single designsGA.txt file with all generated designs
    return write_designs_to_file(all_generated_designs, output_file, verbose)

# Run the genetic algorithm when script is executed directly
if __name__ == "__main__":
    run_genetic_algorithm()
