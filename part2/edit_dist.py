#!/usr/bin/env python

# Instructions for use: python edit_dist.py <file1> <file2>

import sys
from tokenize import generate_tokens, TokenError
from StringIO import StringIO

def edit_distance(str1, str2):
    l1, l2 = len(str1), len(str2)

    for i in range(min(l1, l2)):
        if str1[i] != str2[i]:
            str1, str2 = str1[i:], str2[i:]
            l1, l2 = len(str1), len(str2)
            break

    for i in range(1, min(l1, l2)):
        if str1[-i] != str2[-i]:
            if i != 1:
                str1, str2 = str1[:-(i-1)], str2[:-(i-1)]
                l1, l2 = len(str1), len(str2)
            break

    if min(l1, l2) == 0:
        return max(l1, l2)

    prev = []
    for i in range(0, l2 + 1):
        prev.append(i)

    sys.stdout.write('Please hold on...')

    for i in range(1, l1 + 1):
        curr = [i] + [0] * l2
        if i % 100 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        for j in range(1, l2 + 1):
            curr[j] = min(prev[j] + 1,
                          curr[j-1] + 1,
                          prev[j-1] + (0 if str1[i-1] == str2[j-1] else 1))
        prev = curr

    print
    return prev[-1]

def fix_line_endings(code):
    return code.replace('\r','')

def get_tokens(code):
    tokens = []
    try:
        for x in generate_tokens(StringIO(code).readline): 
            tokens.append((x[0], x[1]))
    except TokenError:
        pass
    return tokens

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print 'Usage: python edit_dist.py <file1> <file2>'
    else:
        sys.stderr.write('Note: Any unusual attempt to neutralize precise measurement of this script will be considered cheating. This includes, but not limited to, use of eval(), execfile(), os.system(), etc.\n')
        code1 = fix_line_endings(open(sys.argv[1], 'rb').read())
        code2 = fix_line_endings(open(sys.argv[2], 'rb').read())
        tokens1 = get_tokens(code1)
        tokens2 = get_tokens(code2)
        dist = edit_distance(tokens1, tokens2)
        print 'Difference: %d token(s)' % dist
