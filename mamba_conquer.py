import sys
import shutil
import random
import argparse
from collections import defaultdict
import libmambapy
from mamba.utils import load_channels, init_api_context, get_installed_jsonfile

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def read_environment(filename):
    with open(filename,  'r') as env_file:
        env = load(env_file, Loader=Loader)
    return env


def join_packages(packages):
    return ','.join(packages)


class MambaSolver:

    def __init__(self, channels):
        init_api_context()

        self.repos = []

        self.prefix = shutil.which('mamba')

        installed_json_f, installed_pkg_recs = get_installed_jsonfile(self.prefix)

        self.channels = channels
        self.pool = libmambapy.Pool()
        self.index = load_channels(self.pool, self.channels, self.repos)

        repo = libmambapy.Repo(self.pool, "installed", installed_json_f.name, "")
        repo.set_installed()
        self.repos.append(repo)

    def solve(self, specs):

        solver_options = [(libmambapy.SOLVER_FLAG_ALLOW_DOWNGRADE, 1)]
        solver = libmambapy.Solver(self.pool, solver_options)

        solver.add_jobs(specs, libmambapy.SOLVER_INSTALL)

        print('Solving: %s' % join_packages(specs))
        success = solver.solve()
        print('Success: %s' % success)
        problems = ''

        if not success:
            problems = solver.problems_to_str()

        return success, problems


class MambaProblem:

    def __init__(self, packages, important_packages=None):

        self.important_packages = []
        if important_packages is not None:
            self.important_packages = important_packages
        self.update_packages(packages)

    def update_packages(self, packages):
        self.packages = packages
        self.all_packages = self.packages + self.important_packages

    def solve(self, solver):

        return solver.solve(self.all_packages)

    def shuffle(self):

        random.shuffle(self.packages)

    def split(self):

        split_index = len(self.packages) // 2

        new_problem = MambaProblem(self.packages[split_index:], important_packages=self.important_packages)
        self.update_packages(self.packages[:split_index])

        return [self, new_problem]

    def join(self, problem):

        self.update_packages(self.packages + problem.packages)

    def __len__(self):

        return len(self.packages)

    def __str__(self):

        return 'MambaProblem: %s' % join_packages(self.packages)


def split_problem(problem, npackages=5):
    problems = [problem]
    while min(map(len, problems)) > npackages:
        new_problems = []
        for problem in problems:
            new_problems.extend(problem.split())
        problems = new_problems
    return problems


def mamba_conquer(environment, important_packages=None, npackages=5):

    env = read_environment(environment)

    dependencies = env['dependencies']
    channels = env['channels']

    solver = MambaSolver(channels)

    random.shuffle(dependencies)

    if important_packages is not None:
        important_packages = important_packages

    problems = split_problem(MambaProblem(dependencies, important_packages=important_packages), npackages)

    results = defaultdict(list)
    for problem in problems:
        success, build_problems = problem.solve(solver)
        results[success].append({
            'packages': problem.packages,
            'problems': build_problems,
        })

    print('Following builds were successful:\n')
    for build in results[True]:
        print('Packages: %s\n' % join_packages(build['packages']))
    print('Following builds were unsuccessful:\n')
    for build in results[False]:
        print(('Packages: %s\n'
               'Problems: %s\n') % (join_packages(build['packages']),
                                    build['problems']))


if __name__ == "__main__":

    specs = ['numpy', 'mamba']

    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', type=str,
                        help='Environment file to solve')
    parser.add_argument('-n', '--npackages', type=int, default=5,
                        help='Number of packages to solve per environment')
    parser.add_argument('packages', type=str, nargs='*', default=[],
                        help='Important packages for each solve')

    args = parser.parse_args()

    if args.env is None:
        print('Environment file needed!')
        sys.exit(1)

    mamba_conquer(args.env, important_packages=args.packages, npackages=args.npackages)
