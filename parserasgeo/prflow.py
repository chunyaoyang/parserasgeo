from .features.boundary import Boundary


def format_float_fixed_width(val, width=8):
    """
    Format a float with right alignment and dynamic decimal precision,
    preserving the total string width.

    Parameters:
    - val (float or str): The numeric value to format.
    - width (int): Total width of the resulting string (default = 8).

    Returns:
    - str: Formatted string of length `width`.
    """
    val_f = float(val)
    if '.' in str(val):
        decimals = len(str(val).split('.')[1])
    else:
        decimals = 0

    # Ensure decimals don't exceed the width minus at least 1 digit and decimal point
    decimals = min(decimals, max(0, width - 2))
    return f"{val_f:>{width}.{decimals}f}"



class SteadyFlow:
    """
    Imports and modifies HEC-RAS steady flow data (*.f??).
    """
    def format_float_fixed_width(val, width=8):
        """
        Format a float as a string with right alignment and dynamic decimal precision,
        preserving the total character width.

        Parameters:
        - val (float or str): The numeric value to format.
        - width (int): Total width of the resulting string (default is 8).

        Returns:
        - str: Formatted string of length `width`.
        """
        val_f = float(val)
        if '.' in str(val):
            decimals = len(str(val).split('.')[1])
        else:
            decimals = 0
        fmt = f"{{val:>{width}.{decimals}f}}"
        return fmt.format(val=val_f)

    def __init__(self, filename):
        self.filename = filename
        self.flow_list = []
        self.flow_title = ""
        self.program_version = ""
        self.num_of_prof = 0
        self.river_name = ""
        self.reach_name = ""
        self.profile_names = []
        self.flow_values_line_idx = None
        self.profile_names_line_idx = None
        self.num_of_prof_line_idx = None
        self.boundary_end_index = None
        self._parse()

    def _parse(self):
        """
        Parses the steady flow file into flow_list.
        Identifies key header values and indexes for later updates.
        """
        with open(self.filename, "rt") as infile:
            for idx, line in enumerate(infile):
                self.flow_list.append(line)

                if line.startswith("Flow Title"):
                    self.flow_title = line.strip().split("=", 1)[-1]
                elif line.startswith("Program Version"):
                    self.program_version = line.strip().split("=", 1)[-1]
                elif line.startswith("Number of Profiles"):
                    self.num_of_prof = int(line.strip().split("=", 1)[-1])
                    self.num_of_prof_line_idx = idx
                elif line.startswith("Profile Names"):
                    self.profile_names = [p.strip() for p in line.strip().split("=", 1)[-1].split(',')]
                    self.profile_names_line_idx = idx
                elif "River Rch & RM=" in line:
                    tokens = line.strip().split(',')
                    if len(tokens) >= 2:
                        self.river_name = tokens[0].replace("River Rch & RM=", "").strip()
                        self.reach_name = tokens[1].strip()
                    self.flow_values_line_idx = idx + 1

        # Locate the start of the boundary block
        for idx, line in enumerate(self.flow_list):
            if line.strip().startswith("Boundary for River Rch & Prof#"):
                self.boundary_end_index = idx + 4
                break

    def edit_profile(self, index, discharge, name=None):
        """
        Edits the discharge and optionally the name of an existing profile.
        Updates Lines 4 and 6 (Profile Names and Discharge).
        """
        if index < 0 or index >= self.num_of_prof:
            raise IndexError("Invalid profile index.")

        # Update discharge
        flows = self.flow_list[self.flow_values_line_idx].split()
        flows[index] = str(discharge)
        self.flow_list[self.flow_values_line_idx] = ''.join([format_float_fixed_width(val, 8) for val in flows]) + '\n'



        # Update profile name if provided
        if name:
            self.profile_names[index] = name
        updated_names = ','.join(self.profile_names)
        self.flow_list[self.profile_names_line_idx] = f"Profile Names={updated_names}\n"

    def add_profile(self, discharge, name):
        """
        Adds a new profile with specified discharge and name.
        Updates Lines 3, 4, and 6.
        """
        self.num_of_prof += 1
        self.flow_list[self.num_of_prof_line_idx] = f"Number of Profiles= {self.num_of_prof} \n"

        # Append new name
        self.profile_names.append(name)
        updated_names = ','.join(self.profile_names)
        self.flow_list[self.profile_names_line_idx] = f"Profile Names={updated_names}\n"

        # Add new discharge value
        flows = self.flow_list[self.flow_values_line_idx].split()
        flows.append(str(discharge))
        self.flow_list[self.flow_values_line_idx] = ''.join([format_float_fixed_width(val, 8) for val in flows]) + '\n'




    def add_internal_change_line(self, river_station: float | int, ws_change: float | int):
        """
        Adds a formatted 'Set Internal Change=' line using flow file metadata.
        Inserts after boundary block if none exists, or sorted by station if it does.
        """
        river_name = self.river_name.ljust(16)
        reach_name = self.reach_name.ljust(16)
        station = f"{river_station}".ljust(8)
        profile = " 1 "
        type_code = " 4 "
        ws_amt = f"{ws_change}".ljust(8)
        ic_line = f"Set Internal Change={river_name},{reach_name},{station},{profile},{type_code},{ws_amt}\n"

        ic_indices = []
        for idx, line in enumerate(self.flow_list):
            if isinstance(line, str) and line.startswith("Set Internal Change="):
                try:
                    station_val = float(line.strip().split(',')[2])
                except ValueError:
                    station_val = -1
                ic_indices.append((idx, station_val))

        if not ic_indices:
            insert_index = (self.boundary_end_index + 1) if self.boundary_end_index else 9
            self.flow_list.insert(insert_index, ic_line)
        else:
            new_station_val = float(river_station)
            inserted = False
            for i, (idx, existing_station) in enumerate(ic_indices):
                if new_station_val > existing_station:
                    self.flow_list.insert(idx, ic_line)
                    inserted = True
                    break
            if not inserted:
                last_ic_index = ic_indices[-1][0]
                self.flow_list.insert(last_ic_index + 1, ic_line)

    def export(self, outfilename):
        """
        Writes steady flow data to outfilename.
        """
        with open(outfilename, "wt", newline="\r\n") as outfile:
            for item in self.flow_list:
                outfile.write(str(item))

    def __str__(self):
        """
        Returns the full steady flow file content as a string.
        Enables `print(ffile)` to show the file.
        """
        return ''.join(self.flow_list)


class UnsteadyFlow:
    """
    Imports RAS unsteady flow data in filename, i.e. project_name.u??
    """

    def __init__(self, filename):
        self.filename = filename
        self.uflow_list = []

        with open(filename, "rt") as infile:
            line = infile.readline()
            while line:
                if Boundary.test(line):
                    boundary = Boundary()
                    line = boundary.import_geo(line, infile)
                    self.uflow_list.append(boundary)
                else:
                    self.uflow_list.append(line)
                    line = infile.readline()

    def export(self, outfilename):
        """
        Writes unsteady flow data to outfilename.
        """
        with open(outfilename, "wt", newline="\r\n") as outfile:
            for line in self.uflow_list:
                outfile.write(str(line))

    def get_boundaries(
        self, river=None, reach=None, station_value=None, hydrograph_type=None
    ):
        """Get Boundary instances from unsteady flow
        :param river: Optional string of the name of river
        :param reach: Optional string of the name of reach
        :param station_value: Optional float representing the location of the station or 2-tuple representing a range
        :param hydrograph_type: Optional string matching the boundary hydrograph type
        :return: List of matching Boundary instances
        """
        boundaries = (item for item in self.uflow_list if isinstance(item, Boundary))
        if river is not None:
            boundaries = (bnd for bnd in boundaries if bnd.header.river_name == river)
        if reach is not None:
            boundaries = (bnd for bnd in boundaries if bnd.header.reach_name == reach)
        if station_value is not None:
            if isinstance(station_value, tuple):
                assert len(station_value) == 2
                if station_value[0] is not None:
                    boundaries = (
                        bnd
                        for bnd in boundaries
                        if bnd.header.station.value is not None
                        and bnd.header.station.value >= station_value[0]
                    )
                if station_value[1] is not None:
                    boundaries = (
                        bnd
                        for bnd in boundaries
                        if bnd.header.station.value is not None
                        and bnd.header.station.value <= station_value[1]
                    )
            else:
                boundaries = (
                    bnd
                    for bnd in boundaries
                    if bnd.header.station.value == station_value
                )
        if hydrograph_type is not None:
            boundaries = (
                bnd for bnd in boundaries if bnd.hydrograph.type == hydrograph_type
            )

        return list(boundaries)
