class ParseRASPlan(object):
    def __init__(self, plan_filename):
        self.plan_filename = plan_filename
        self.plan_title = None   # Full plan name
        self.plan_id = None      # Short id
        self.geo_file = None     # geometry file extension: g01, g02, ..
        self.plan_file = None    # flow file extension: f01, f02, ..
        self.other_lines = []

        with open(plan_filename, 'rt') as plan_file:
            for line in plan_file:
                stripped = line.rstrip('\n')
                fields = stripped.split('=')

                if len(fields) == 1:
                    self.other_lines.append(stripped)
                    continue

                var, value = fields[0], fields[1]

                if var == 'Geom File':
                    self.geo_file = value
                elif var == 'Flow File':
                    self.plan_file = value
                elif var == 'Plan Title':
                    self.plan_title = value
                elif var == 'Short Identifier':
                    self.plan_id = value
                else:
                    self.other_lines.append(stripped)

    def __str__(self):
        s = f'Plan Title={self.plan_title}\n'
        s += f'Short Identifier={self.plan_id}\n'
        s += f'Geom File={self.geo_file}\n'
        s += f'Flow File={self.plan_file}\n'
        for line in self.other_lines:
            s += line + '\n'
        return s

    def write(self, output_filename=None):
        if output_filename is None:
            output_filename = self.plan_filename
        with open(output_filename, 'w') as f:
            f.write(str(self))
