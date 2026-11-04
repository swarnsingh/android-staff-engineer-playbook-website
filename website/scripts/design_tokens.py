"""Compile design-system values without changing CSS variable scope or units.

Values such as `var(--actor)` must resolve on the consuming element, not on
:root. Build-time substitutions also work in media queries and SVG geometry.
"""
from pathlib import Path
import json
import re

WEB=Path(__file__).resolve().parents[1]
TOKEN=re.compile(r'\{\{([a-z][a-z0-9-]*)\}\}')


def component_values():
    result={}
    for row in json.loads((WEB/'design-system/tokens.json').read_text())['componentCss']['tokens']:
        if row['name'] in result:raise ValueError('Duplicate component token: '+row['name'])
        if not isinstance(row['value'],str) or any(c in row['value'] for c in '{};'):
            raise ValueError('A component token must be one CSS value: '+row['name'])
        result[row['name']]=row['value']
    return result


def compile_css(source,values=None):
    values=component_values() if values is None else values
    def replace(match):
        name=match[1]
        if name not in values:raise ValueError('Unknown component token: '+name)
        return values[name]
    result=TOKEN.sub(replace,source)
    if '{{' in result:raise ValueError('Malformed/unexpanded component token')
    return result


def stylesheet_bytes(file):
    return compile_css(file.read_text()).encode()


def geometry_values(rows=None):
    """Keep duplicate names and non-finite geometry out of the SVG renderer."""
    import math
    rows = json.loads((WEB/'design-system/tokens.json').read_text())['figureGeometry']['tokens'] if rows is None else rows
    values = {}
    def valid(value):
        if isinstance(value, bool):return False
        if isinstance(value, (int, float)):return math.isfinite(value)
        if isinstance(value, str):return bool(value) and not any(c in value for c in '<>&"')
        if isinstance(value, dict):return all(re.fullmatch(r'[a-z][a-z_]*', k) and valid(v) for k,v in value.items())
        return isinstance(value, list) and bool(value) and all(valid(v) for v in value)
    for row in rows:
        if row['name'] in values:raise ValueError('Duplicate geometry token: '+row['name'])
        if not valid(row['value']):raise ValueError('Invalid geometry token: '+row['name'])
        values[row['name']] = row['value']
    return values


def check_source(source):
    """Reject new raw lengths, times, angles and partial percentages before expansion.

    Zero, a full-size percentage, and single fractional tracks are structural
    constants. Column counts and algorithmic ratios are declared data parameters.
    """
    masked = re.sub(r'/\*.*?\*/|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'', '', source, flags=re.S)
    masked = TOKEN.sub('', masked)
    measure = re.compile(r'(?<![\w-])(-?(?:\d*\.)?\d+)(px|rem|em|ch|ex|vh|vw|vmin|vmax|dvh|dvw|svh|svw|lvh|lvw|cm|mm|in|pt|pc|ms|s|deg|rad|turn|%|fr)\b|(?<![\w-])(-?(?:\d*\.)?\d+)%')
    for match in measure.finditer(masked):
        number = float(match[1] or match[3]);unit = match[2] or '%'
        if number == 0 or (unit == '%' and number == 100) or (unit == 'fr' and number == 1):continue
        raise ValueError('Raw component dimension: '+match[0]+' (use a component token)')
