import sys
import csv
import os

# File format:
#
# Columns:
#  0. file_name
#  1. prog_name
#  2. verdict_base
#  3. verdict_comp
#  4. verdict_diff
#  5. total_states_base
#  6. total_states_comp
#  7. total_states_diff
#
# Records sample:
#  file-a,a,success,failure,MISMATCH,12,12,+0 (+0.00%)
#  file-b,b,success,success,MATCH,67,67,+0 (+0.00%)

TRESHOLD_PCT = 0

HEADERS = ['file_name', 'prog_name', 'verdict_base', 'verdict_comp',
           'verdict_diff', 'total_states_base', 'total_states_comp',
           'total_states_diff']

FILE        = 0
PROG        = 1
VERDICT_OLD = 2
VERDICT_NEW = 3
STATES_OLD  = 5
STATES_NEW  = 6

if len(sys.argv) == 2:
    CSV_PATH = sys.argv[1]
else:
    print(f'Usage: {sys.argv[0]} <compare.csv>>')
    sys.exit(1)

if not os.path.exists(CSV_PATH):
    print(f'# {CSV_PATH} does not exist, failing step')
    sys.exit(1)

def read_table(path):
    with open(path, newline='') as file:
        reader = csv.reader(file)
        headers = next(reader)
        if headers != HEADERS:
            raise Exception(f'Unexpected table header for {path}: {headers}')
        return list(reader)

table = read_table(CSV_PATH)
new_failures = False
changes = False
headers = ['File', 'Program', 'Verdict', 'States Diff (%)']
html_table = [headers]
text_table = [headers]

def compute_diff(v):
    old = int(v[STATES_OLD]) if v[STATES_OLD] != 'N/A' else 0
    new = int(v[STATES_NEW]) if v[STATES_NEW] != 'N/A' else 0
    if old == 0:
        return 1
    return (new - old) / old

for v in table:
    add = False
    html_verdict = v[VERDICT_NEW]
    text_verdict = v[VERDICT_NEW]
    diff = compute_diff(v)

    if v[VERDICT_OLD] != v[VERDICT_NEW]:
        changes = True
        add = True
        html_verdict = f'{v[VERDICT_OLD]} &rarr; {v[VERDICT_NEW]}'
        text_verdict = f'{v[VERDICT_OLD]} -> {v[VERDICT_NEW]}'
        if v[VERDICT_NEW] == 'failure':
            new_failures = True
            html_verdict += ' :bangbang:'
            text_verdict += ' (!!)'

    if abs(diff * 100) > TRESHOLD_PCT:
        changes = True
        add = True

    if not add:
        continue

    diff_txt = '{:+.1f} %'.format(diff * 100)
    html_table.append([v[FILE], v[PROG], html_verdict, diff_txt])
    text_table.append([v[FILE], v[PROG], text_verdict, diff_txt])

def print_table(rows, fn):
    column_widths = [0] * len(rows[0])
    for row in rows:
        for i, col in enumerate(row):
            column_widths[i] = max(column_widths[i], len(col))

    def print_row(row):
        line = '|'
        for width, col in zip(column_widths, row):
            line += ' ' + col.ljust(width) + ' |'
        fn(line)

    rows_iter = iter(rows)
    print_row(next(rows_iter))

    underscores = '|'
    for width in column_widths:
        underscores += '-' * (width + 2) + '|'
    fn(underscores)

    for row in rows_iter:
        print_row(row)

if new_failures:
    section_name = '# There are new veristat failures'
elif changes:
    section_name = '# There are changes in verification performance'
else:
    section_name = '# No changes in verification performance'

# Print the step summary

if summary_path := os.getenv('GITHUB_STEP_SUMMARY', None):
    summary_file = open(summary_path, 'a')

def print_summary(s = ''):
    if summary_file:
        summary_file.write(f'{s}\n')

print_summary(section_name)
print(section_name)

if new_failures or changes:
    print()
    print_table(text_table, print)
    print()

    print_summary()
    print_summary('<details>')
    print_summary('<summary>Click to expand</summary>')
    print_summary()
    print_table(html_table, print_summary)
    print_summary()
    print_summary('</details>')

if new_failures:
    print('Failing step because of the new failures')
    sys.exit(1)
