from .features.boundary import Boundary


class SteadyFlow:
    """
    Imports and modifies HEC-RAS steady flow data (*.f??).
    """

    def __init__(self, filename):
        self.filename = filename
        self.flow_list = []
        self.flow_title = ""
        self.program_version = ""
        self.num_of_prof = 0
        self.river_name = ""
        self.reach_name = ""
        self.boundary_end_index = None
        self._parse()

    def _parse(self):
        """
        Parses the steady flow file into flow_list.
        Uses explicit header keywords to identify: Flow Title, Program Version, Number of Profiles.
        Identifies the end of the boundary section.
        """
        with open(self.filename, "rt") as infile:
            line_index = 0
            while True:
                line = infile.readline()
                if not line:
                    break
                self.flow_list.append(line)

                if line.startswith("Flow Title"):
                    self.flow_title = line.strip().split("=", 1)[-1]
                elif line.startswith("Program Version"):
                    self.program_version = line.strip().split("=", 1)[-1]
                elif line.startswith("Number of Profiles"):
                    self.num_of_prof = int(line.strip().split("=", 1)[-1])

                # Capture river and reach name from River Rch & RM line (typically line 5)
                if line.startswith("River Rch & RM="):
                    tokens = line.strip().split(',')
                    if len(tokens) >= 2:
                        self.river_name = tokens[0].replace("River Rch & RM=", "").strip()
                        self.reach_name = tokens[1].strip()

                line_index += 1

        # Locate the start of the boundary block
        boundary_start_index = None
        for idx, line in enumerate(self.flow_list):
            if line.strip().startswith("Boundary for River Rch & Prof#"):
                boundary_start_index = idx
                break

        if boundary_start_index is None:
            raise ValueError("Could not locate 'Boundary for River Rch & Prof#' section in the file.")

        self.boundary_end_index = boundary_start_index + 5 - 1

    def add_internal_change_line(self, river_station: float | int, ws_change: float | int):
        """
        Adds a formatted 'Set Internal Change=' line using flow file metadata.
        Inserts after boundary block if none exists, or sorted by station if it does.
        """
        river_name = self.river_name.ljust(16)
        reach_name = self.reach_name.ljust(16)
        station = f"{river_station}".ljust(8)
        profile = " 1 "  # Default flow profile
        type_code = " 4 "  # Default type
        ws_amt = f"{ws_change}".ljust(8)

        ic_line = f"Set Internal Change={river_name},{reach_name},{station},{profile},{type_code},{ws_amt}\n"

        # Find all existing internal change lines and their stations
        ic_indices = []
        for idx, line in enumerate(self.flow_list):
            if isinstance(line, str) and line.startswith("Set Internal Change="):
                try:
                    station_val = float(line.strip().split(',')[2])
                except ValueError:
                    station_val = -1  # fallback if parsing fails
                ic_indices.append((idx, station_val))

        if not ic_indices:
            insert_index = (self.boundary_end_index + 1) if self.boundary_end_index is not None else 9
            self.flow_list.insert(insert_index, ic_line)
        else:
            # Insert so that highest river_station appears first
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
