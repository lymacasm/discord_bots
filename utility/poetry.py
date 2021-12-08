class PoetryError(Exception):
    pass

class SyllableSchemeMismatchError(PoetryError):
    pass

def get_syllable_count(word: str):
    """ Counts the number of syllables in the input word. """
    word = word.lower().replace('.', '').replace(',', '').replace('!', '').replace('?', '')
    count = 0
    vowels = 'aeiouy'
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith('e') and not word.endswith('le'):
        count -= 1
    if count == 0:
        count += 1
    return count

def matches_syllables_scheme(potential_poetry: str, syllable_counts: list[int]) -> list[str]:
    """
    Checks to see if input string matches the provided syllable scheme.
    Throws SyllableSchemeMismatchError if the potential_poetry scheme doesn't match.

        Parameters:
            potential_poetry (str): Input string to check against.
            syllable_counts (list[str]): List of syllable counts per line. For example, a haiku, which
                has 3 lines of 5 syllables -> 7 syllables -> 5 syllables, would be input as a list as follows:
                    [5, 7, 5]
        
        Returns:
            poetry_lines (list[str]): Input string split into lines of poetry.
        
        Exceptions:
            Throws:
                - SyllableSchemeMismatchError
    """
    words = potential_poetry.strip().split(' ')
    lines = [[]]
    syllables = list(syllable_counts)
    line_idx = 0
    for word in words:
        if line_idx >= len(syllables):
            raise SyllableSchemeMismatchError('Extra syllables in input string.')
        elif line_idx >= len(lines):
            lines.append([])

        lines[line_idx].append(word)
        syllables[line_idx] -= get_syllable_count(word)

        if syllables[line_idx] < 0:
            raise SyllableSchemeMismatchError(f'Too many syllables in line {line_idx}.')
        if syllables[line_idx] == 0:
            line_idx += 1

    if not all(rem_syl == 0 for rem_syl in syllables):
        raise SyllableSchemeMismatchError('Not enough syllables in input string.')
    return [' '.join(line) for line in lines]
