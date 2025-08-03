class ParseRASProject:
    def __init__(self, project_filename):
        self.project_filename = project_filename
        self.header_lines = []      # First 4 lines
        self.geom_files = []
        self.flow_files = []
        self.plan_files = []
        self.tail_lines = []        # All lines after plan files

        with open(project_filename, 'r') as f:
            lines = f.readlines()

        self.header_lines = lines[:4]

        for line in lines[4:]:
            line_stripped = line.strip()
            if line_stripped.startswith('Geom File='):
                self.geom_files.append(line_stripped)
            elif line_stripped.startswith('Flow File='):
                self.flow_files.append(line_stripped)
            elif line_stripped.startswith('Plan File='):
                self.plan_files.append(line_stripped)
            else:
                self.tail_lines.append(line.rstrip('\n'))

    def insert_entry(self, entries):
        if isinstance(entries, str):
            entries = [entries]

        for entry in entries:
            if len(entry) != 3 or not entry[1:].isdigit():
                continue

            kind = entry[0].lower()
            line = f"{self._label(kind)}={entry}"
            target_list = self._target_list(kind)

            if target_list is None:
                continue

            existing = [l.split('=')[1] for l in target_list]
            if entry not in existing:
                target_list.append(line)
                target_list.sort(key=lambda x: int(x.split('=')[1][1:]))

    def change_plan(self, new_id):
        if not (isinstance(new_id, str) and len(new_id) == 2 and new_id.isdigit()):
            raise ValueError(f"Invalid plan ID: {new_id}")

        new_code = f"p{new_id}"
        existing_codes = [line.split('=')[1] for line in self.plan_files]

        if new_code not in existing_codes:
            raise ValueError(f"Plan File={new_code} not found in project.")

        self.header_lines[1] = f"Current Plan={new_code}\n"

    def _target_list(self, kind):
        if kind == 'g':
            return self.geom_files
        elif kind == 'f':
            return self.flow_files
        elif kind == 'p':
            return self.plan_files
        else:
            return None

    def _label(self, kind):
        return {'g': 'Geom File', 'f': 'Flow File', 'p': 'Plan File'}[kind]

    def write(self, output_filename=None):
        if output_filename is None:
            output_filename = self.project_filename

        with open(output_filename, 'w') as f:
            for line in self.header_lines:
                f.write(line if line.endswith('\n') else line + '\n')
            for line in self.geom_files:
                f.write(line + '\n')
            for line in self.flow_files:
                f.write(line + '\n')
            for line in self.plan_files:
                f.write(line + '\n')
            for line in self.tail_lines:
                f.write(line + '\n')
