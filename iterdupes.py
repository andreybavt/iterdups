#!/home/andrey/anaconda3/bin/python3

import argparse
import os
import pickle
import shutil
import subprocess
from copy import deepcopy


def rm_r(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)


def find_dupes(dir, minsize):
    output = subprocess.run(["fdupes", "-S", "-n", "-r", dir], stdout=subprocess.PIPE).stdout.decode()
    files = output.split('\n\n')
    result = []
    for f in files:
        if len(f):
            size_bytes = int(f.split('\n')[0].split(' ')[0])
            paths = f.split('\n')[1:]
            result.append({'size': size_bytes, 'files': paths})
    res = sorted([f for f in result if f['size'] >= minsize * 1024 * 1024], key=lambda x: x['size'], reverse=True)
    files_to_delete = deepcopy(res)
    total_saved_space = 0
    for f in files_to_delete:
        f['files'] = sorted(f['files'])
        total_saved_space += f['size'] * (len(f['files']) - 1)
    total_saved_space = total_saved_space
    summary = {'total_saved_space': total_saved_space, 'files_to_delete': files_to_delete, 'scanned_dir': dir}
    write_summary_to_files(summary)


def write_summary_to_files(summary):
    with open('dupes-report.log', 'w') as f:
        f.write('Scan root: %s\n' % summary['scanned_dir'])
        f.write('Saved space (Mb): {}\n\n'.format(summary['total_saved_space'] / 1024 ** 2))  # Mbytes
        f.write('\n'.join(
            ['\/' * 5 + str(f['size']) + '\/' * 5 + '\n' + '\n'.join(f['files']) + '\n' + '/\\' * 10
             for f in summary['files_to_delete']]))
    with open('files_to_delete.pkl', 'wb') as f:
        pickle.dump(summary, f)


def skip_or_remove(root, mode=None):
    with open('files_to_delete.pkl', 'rb') as f:
        summary = pickle.load(f)
    original_total_saved_space = summary['total_saved_space']
    for files in summary['files_to_delete']:
        matching_files = [f for f in files['files'] if f.startswith(root)]
        remaining_files = [f for f in files['files'] if not f.startswith(root)]
        if mode and matching_files:
            for mf in matching_files:
                print(('(SIMULATION) ' if mode == 'sim' else '') + 'Deleting: ' + mf)
                if mode == 'rm':
                    rm_r(mf)
        not_saved_space = (len(files['files']) - len(remaining_files)) * files['size']
        files['files'] = remaining_files
        summary['total_saved_space'] -= not_saved_space
    summary['files_to_delete'] = [f for f in summary['files_to_delete'] if len(f['files']) > 1]
    if mode == 'sim':
        print('\n\nDeleted Bytes:' + str(original_total_saved_space - summary['total_saved_space']))
    else:
        write_summary_to_files(summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('mode', nargs=1, default='scan', help='scan, skip, rm, sim')
    parser.add_argument('-p', help='Duplicate search root path')
    parser.add_argument('-s', help='Min size of a file, MB', default=0)

    args = parser.parse_args()

    if args.mode[0] == 'scan':
        find_dupes(args.p, float(args.s))
    if args.mode[0] == 'skip':
        skip_or_remove(args.p)
    if args.mode[0] == 'rm' or args.mode[0] == 'sim':
        skip_or_remove(args.p, args.mode[0])

    # command = sys.argv[1]
    # if command == 'scan':
    #
    # elif command == 'clean':
    #     operation = sys.argv[2]
    #     if operation == 'skip':
    #         path = sys.argv[3]
    #         with open('dupes-report.log', 'r') as f:
    #             report = f.read()
    #         new_report_paths = [p for p in report.split('\n\n')[1].split('\n') if not p.startswith(path)]
    #         with open('dupes-report.log', 'w') as f:
    #             f.write('{}\n\n{}'.format(report.split('\n\n')[0], '\n'.join(new_report_paths)))
    #         print('Remaining files to remove: {}'.format(len(new_report_paths)))
