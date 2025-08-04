import numpy as np

def load_specslab_xy(
    filepath: str,
    comment_prefix: str = '#',
    delimiter = None,
    apply_transmission: bool = False
) -> np.ndarray:

    result, _ = load_specslab_xy_with_error_bars(filepath, comment_prefix, delimiter, apply_transmission)
    return result


def load_specslab_xy_with_error_bars(
    filepath: str,
    comment_prefix: str = '#',
    delimiter = None,
    apply_transmission: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    wip_flags = {
        "Separate Scan Data": "yes",
        "Separate Channel Data": "yes",
    }

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Check for WIP flags in comment lines
    for line in lines:
        if line.strip().startswith(comment_prefix):
            for key, value in wip_flags.items():
                if key in line and value in line.lower():
                    raise NotImplementedError(f"Work in progress: '{key}' is set to 'yes'.")

    # Find column labels
    column_labels = None
    for line in lines:
        if line.strip().startswith(comment_prefix) and 'ColumnLabels:' in line:
            label_line = line.split('ColumnLabels:')[1].strip()
            column_labels = label_line.split()
            break

    if column_labels is None:
        raise ValueError("ColumnLabels line not found in the file.")

    # Map column names to their indices
    col_indices = {label: i for i, label in enumerate(column_labels)}

    if 'energy' not in col_indices or 'counts/s' not in col_indices:
        raise ValueError("Required columns 'energy' and 'counts/s' not found.")

    # Filter data lines
    data = np.loadtxt(filepath, comments=comment_prefix,delimiter=delimiter)

    # Extract required columns
    energy = data[:, col_indices['energy']]
    counts = data[:, col_indices['counts/s']]

    # Apply transmission correction if needed
    if apply_transmission and 'transmission' in col_indices:
        transmission = data[:, col_indices['transmission']]
        counts *= transmission

    # Prepare main data array: [energy, counts/s]
    result = np.column_stack((energy, counts))

    # Extract error bars
    if 'ErrorBar' in col_indices:
        error_bar = data[:, col_indices['ErrorBar']]
    else:
        error_bar = data[:, 0] * 0

    return result, error_bar

