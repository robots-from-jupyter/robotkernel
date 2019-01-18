/*
  Copyright (c) 2018 Georgia Tech Research Corporation
  Distributed under the terms of the BSD-3-Clause License
*/

/*
  An implementation of syntax highlighting for robot framework 3.1.

  http://robotframework.org/robotframework/3.1/RobotFrameworkUserGuide.html

  When necessary, the source code is consulted and ultimately trusted:

  https://github.com/robotframework/robotframework
*/

// tslint:disable-next-line
/// <reference path="../typings/codemirror/codemirror.d.ts"/>

// tslint:disable-next-line
import 'codemirror/addon/mode/simple';

import * as CodeMirror from 'codemirror';

/**
  An implementation of the CodeMirror simple mode object

  https://github.com/codemirror/CodeMirror/blob/master/addon/mode/simple.js
*/
interface ISimpleState {
  /** The regular expression that matches the token. May be a string or a regex object. When a regex, the ignoreCase flag will be taken into account when matching the token. This regex has to capture groups when the token property is an array. If it captures groups, it must capture all of the string (since JS provides no way to find out where a group matched). */
  regex: string | RegExp;
  /// An optional token style. Multiple styles can be specified by separating them with dots or spaces. When this property holds an array of token styles, the regex for this rule must capture a group for each array item.
  token?: string | string[] | null;
  /// When true, this token will only match at the start of the line. (The ^ regexp marker doesn't work as you'd expect in this context because of limitations in JavaScript's RegExp API.)
  sol?: boolean;
  /// When a next property is present, the mode will transfer to the state named by the property when the token is encountered.
  next?: string;
  /// Like next, but instead replacing the current state by the new state, the current state is kept on a stack, and can be returned to with the pop directive.
  push?: string;
  /// When true, and there is another state on the state stack, will cause the mode to pop that state off the stack and transition to it.
  pop?: boolean;
  /// Can be used to embed another mode inside a mode. When present, must hold an object with a spec property that describes the embedded mode, and an optional end end property that specifies the regexp that will end the extent of the mode. When a persistent property is set (and true), the nested mode's state will be preserved between occurrences of the mode.
  mode?: {
    spec: string;
    end?: string | RegExp;
    persistent?: boolean;
  };
  /// When true, this token changes the indentation to be one unit more than the current line's indentation.
  indent?: boolean;
  /// When true, this token will pop one scope off the indentation stack.
  dedent?: boolean;
  /// If a token has its dedent property set, it will, by default, cause lines where it appears at the start to be dedented. Set this property to false to prevent that behavior.
  dedentIfLineStart?: boolean;
}

/** A string-keyed set of simple state lists */
export interface IStates {
  [key: string]: ISimpleState[];
}

/** helper function for compactly representing a rule */
function r(
  regex: RegExp,
  token?: string | string[],
  opt?: Partial<ISimpleState>
): ISimpleState {
  return { regex, token, ...opt };
}

/** Possible Robot Framework table names. Group count is important.  */
const TABLE_NAMES: { [key: string]: RegExp } = {
  keywords: /(\|\s)?(\*+\s*)(user keywords?|keywords?)(\s*\**)/i,
  settings: /(\|\s)?(\*+\s*)(settings?)(\s*\**)/i,
  test_cases: /(\|\s)?(\*+\s*)(tasks?|test cases?)(\s*\**)/i,
  variables: /(\|\s)?(\*+\s*)(variables?)(\s*\**)/i
};

/** Enumerate the possible rules  */
const RULES_TABLE: ISimpleState[] = Object.keys(TABLE_NAMES).map(
  (next: string) => {
    return r(
      TABLE_NAMES[next],
      ['bracket', 'header.link', 'header.link', 'header.link'],
      {
        next,
        sol: true
      }
    );
  }
);

/** Pattern to match the start of a variable */
const VAR_START = /[\$&@%]\{/;
/** Pattern to match the end of a variable */
const VAR_END = /\}/;

/** Valid python operators */
const VAR_OP = /[*\-+\\%&|=><!]/;
/** Valid python numbers */
const VAR_NUM = /0(b[01]+|o[0-7]+|x[0-9a-f]+)|(\d+)(\.\d+)?(e-?(\d+)(\.\d+)?)?/i;
/**
    Valid python builtins
    Valid  way out at the end is a lookahead for VAR_OP, end or .
*/
const VAR_BUILTIN = /(none|(cur|temp|exec)dir|\/|:|\\n|true|empty|false|null|space|test (name|documentation|status|message|tags)|prev test (name|status|message)|suite (name|source|documentation|status|message|metadata)|keyword (status|message)|(report|debug) file|log (file|level)|output (dir|file))(?=[.}]|\s+[*\-+\\%&|=><!])/i;

/** a rule for the beginning of the variable state */
const RULE_VAR_START = r(VAR_START, 'variable', { push: 'variable' });
/** a rule for the end of the variable state */
const RULE_VAR_END = r(VAR_END, 'variable');

/** a rule for a number */
const RULE_NUM = r(VAR_NUM, 'number');

/** a rule for starting a single quote */
const RULE_SINGLE_STRING_START = r(/'/, 'string', { push: 'single_string' });
/** a rule for starting a double quote */
const RULE_DOUBLE_STRING_START = r(/"/, 'string', { push: 'double_string' });

/** a rule for capturing tags (and friends) in keyword/test/task definitions */
const RULE_TAGS = r(
  /([| ]* *)(\[\s*)(tags)(\s*\])( *\|?)/i,
  ['bracket', 'atom', 'atom', 'atom', 'bracket'],
  { sol: true, push: 'tags' }
);

/** rule for special case of applying tags at the suite level */
const RULE_SUITE_TAGS = r(/(force tags|default tags)(  +)/i, ['atom', null], {
  push: 'tags',
  sol: true
});
/** rule for special case of applying tags at the suite level (with pipes) */
const RULE_SUITE_TAGS_PIPE = r(
  /(\| +)(force tags|default tags)( *\|?)/i,
  ['bracket', 'atom', 'bracket'],
  { sol: true, push: 'tags' }
);

/** rule for bracketed settings of keyword/test/task */
const RULE_SETTING_KEYWORD = r(
  /([| ]* *)(\[\s*)(setup|teardown|template)(\s*\])( *\|?)/i,
  ['bracket', 'atom', 'atom', 'atom', 'bracket'],
  { push: 'keyword_invocation', sol: true }
);

/** rule for bracketed settings of keyword/test/task that include a keyword */
const RULE_SUITE_SETTING_KEYWORD = r(
  /(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)(  +)/i,
  ['atom', null],
  { push: 'keyword_invocation', sol: true }
);

/** rule for bracketed settings of keyword/test/task that include a keyword (with pipes) */
const RULE_SUITE_SETTING_KEYWORD_PIPE = r(
  /(\| +)(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)( +\|)/i,
  ['bracket', 'atom', 'bracket'],
  { push: 'keyword_invocation', sol: true }
);

/** collects the states that we build */
const states: IStates = {};

/** base isn't a state. these are the "normal business" that any state might use */
const base = [
  ...RULES_TABLE,
  RULE_VAR_START,
  RULE_VAR_END,
  r(/\|/, 'bracket'),
  r(/[\.]{3}/, 'bracket'),
  r(/#.*$/, 'comment'),
  r(/\\ +/, 'bracket'),
  r(/\\(?=$)/, 'bracket'),
  r(/([^ =]*)(=)/, ['attribute', 'operator']),
  r(/_\*.*?\*_/, 'string.strong.em'),
  r(/\*.*?\*/, 'string.strong'),
  r(/\_.*?\_/, 'string.em'),
  // this is pretty extreme, but seems to work
  r(/[^ \$]+/, 'string')
];

/** the starting state (begining of a file) */
states.start = [
  r(/(%%python)( module )?(.*)?/, ['meta', 'keyword', 'variable'], {
    mode: { spec: 'ipython' },
    sol: true
  }),
  r(/(%%[^ ]*).*$/, 'meta', { sol: true }),
  ...base
];

/** settings states */
states.settings = [
  RULE_SUITE_TAGS_PIPE,
  RULE_SUITE_TAGS,
  RULE_SUITE_SETTING_KEYWORD_PIPE,
  RULE_SUITE_SETTING_KEYWORD,
  r(
    /(\|* *)(library|resource|variables|documentation|metadata|test timeout|task timeout)( *)/i,
    ['bracket', 'atom', null],
    { sol: true }
  ),
  ...base
];

/** pattern for starting keywords */
const KEY_START = /(  +)/;
/** pattern for starting keywords (with pipes) */
const KEY_START_PIPE = /(\| *\|)( +)/;
/** pattern for starting behavior-driven-development keywords */
const KEY_BDD_START = /(\| *\| *|  +)?(given|when|then|and|but)/i;

/** rule for behavior-driven-development keywords */
const RULE_START_BDD = r(KEY_BDD_START, ['bracket', 'builtin.em'], {
  push: 'keyword_invocation',
  sol: true
});
/** rule for whitespace keywords */
const RULE_KEY_START = r(KEY_START, null, {
  push: 'keyword_invocation',
  sol: true
});
/** rule for pipe keywords */
const RULE_KEY_START_PIPE = r(KEY_START_PIPE, ['bracket', null], {
  push: 'keyword_invocation',
  sol: true
});

/** rules for capturing individual tags */
states.tags = [
  r(/ \| */, 'bracket'),
  r(/^($|\n)/, null, { pop: true }),
  RULE_VAR_START,
  r(/\}(?=$)/, 'variable', { pop: true }),
  RULE_VAR_END,
  r(/^ *(?=$)/, null, { pop: true }),
  r(/ +/, null),
  r(/[^\$&%@]*?(?=(  +| \|))/, 'tag'),
  r(/[^\$&%@]*?(?= *\|?$)/, 'tag', { pop: true }),
  // fall back to single char
  r(/[^\$&%@|]/, 'tag')
];

/** rules for data rows inside a keyword definition */
states.keywords = [
  RULE_TAGS,
  RULE_SETTING_KEYWORD,
  r(
    /([\| ]* *)(\[\s*)(arguments|documentation|return|timeout)(\s*\])( *\|?)/i,
    ['bracket', 'atom', 'atom', 'atom', 'bracket'],
    { sol: true }
  ),
  RULE_START_BDD,
  RULE_KEY_START_PIPE,
  RULE_KEY_START,
  r(/\| (?=[^ ]*\|)/, null, { sol: true, push: 'keyword_invocation' }),
  r(/(?=[^ ])/, null, { sol: true, push: 'keyword_invocation' }),
  ...base
];

/** rules for data rows inside test/task definition */
states.test_cases = [
  RULE_TAGS,
  RULE_SETTING_KEYWORD,
  r(
    /([\| ]* *)(\[\s*)(documentation|timeout)(\s*\])/i,
    ['bracket', 'atom', 'atom', 'atom'],
    { sol: true }
  ),
  RULE_START_BDD,
  RULE_KEY_START_PIPE,
  RULE_KEY_START,
  r(
    /(\| +)([^ *\|\.][^\|]*?)( *)(\|?$)/,
    ['bracket', 'string.header', 'bracket'],
    {
      sol: true
    }
  ),
  r(/(\| +)(.+?)( \| )/, ['bracket', 'string.header', 'bracket'], {
    sol: true
  }),
  r(/([^| *].+$)/, 'string.header', { sol: true }),
  ...base
];

/** rules for inside of an invoked keyword instance */
states.keyword_invocation = [
  r(/^(?= *$)/, null, { pop: true }),
  RULE_VAR_START,
  r(/\}(?=$)/, 'variable', { pop: true }),
  RULE_VAR_END,
  r(/#.*$/, 'comment', { pop: true }),
  r(/( \| |  +)/, 'bracket', { pop: true }),
  r(/ ?=(  +)/, 'operator'),
  r(/(\\|[\.]{3}) +/, 'bracket', { pop: true }),
  r(/ /, null),
  r(/([^ ]*?(?=[\$&%@]\{))/i, 'keyword'),
  r(/[^ \|]+(?=$|[|])/, 'keyword', { pop: true }),
  r(/([^\n\$ *=\|]+?(?= ))/i, 'keyword'),
  ...base
];

/** curious rule for the variables table */
states.variables = [...base];

/** rules for inside of a variable reference */
states.variable = [
  RULE_VAR_START,
  r(VAR_BUILTIN, 'builtin'),
  RULE_NUM,
  r(VAR_OP, 'operator'),
  r(/\./, 'operator', { push: 'variable_property' }),
  r(/\[/, 'bracket', { next: 'variable_index' }),
  r(/\}(?=\[)/, 'variable'),
  r(/[^}\n$]/, 'variable'),
  r(/^(?=\})/, 'variable', { pop: true })
];

/** rules for extended syntax in a variable reference */
states.variable_property = [
  RULE_VAR_START,
  RULE_VAR_END,
  RULE_NUM,
  RULE_SINGLE_STRING_START,
  RULE_DOUBLE_STRING_START,
  r(VAR_OP, 'operator'),
  r(/\(/, 'bracket'),
  r(/\)/, 'bracket', { pop: true }),
  r(/([a-z_][a-z_\d]*)(=)/i, ['variable', 'operator']),
  r(/,/, 'punctuation'),
  r(/[^}](?=\})/, 'property', { pop: true }),
  r(/(^\})( *(?=$|\n))/, ['bracket', null], { pop: true }),
  r(/^ *(?=$|\n)/, null, { pop: true }),
  r(/[^}]/, 'property')
];

/** rules for strings with single quotes */
states.single_string = [
  r(/\\'/, 'string'),
  r(/'/, 'string', { pop: true }),
  r(/./, 'string')
];
/** rules for strings with double quotes */
states.double_string = [
  r(/\\"/, 'string'),
  r(/"/, 'string', { pop: true }),
  r(/./, 'string')
];

/** rules for square-bracketed index referencing */
states.variable_index = [
  RULE_VAR_START,
  RULE_VAR_END,
  RULE_NUM,
  r(/\[/, 'bracket'),
  r(/\](?=\])/, 'bracket'),
  r(/(\])(\})( ?=?)/, ['bracket', 'variable', 'operator'], { pop: true }),
  r(/(\])(\[)/, 'bracket'),
  r(/\]/, 'bracket', { pop: true }),
  r(/[^\]]/, 'string')
];

/** well-known mime type for robot framework (pygments, etc.) */
export const MIME_TYPE = 'text/x-robotframework';
/** the canonical CodeMirror mode name */
export const MODE_NAME = 'robotframework';
/** the human-readable name of the CodeMirror mode */
export const MODE_LABEL = 'robotframework';
/** primary file extension */
export const DEFAULT_EXTENSION = 'robot';
/** all recognized file extensions */
export const EXTENSIONS = [DEFAULT_EXTENSION, 'resource'];

/** the actual exported function that will install the mode in CodeMirror */
export function defineRobotMode() {
  const _CodeMirror = CodeMirror as any;
  _CodeMirror.defineSimpleMode(MODE_NAME, {
    meta: {
      dontIndentStates: ['comment'],
      lineComment: '#'
    },
    ...states
  });

  CodeMirror.defineMIME(MIME_TYPE, MODE_NAME);

  CodeMirror.modeInfo.push({
    ext: EXTENSIONS,
    mime: MIME_TYPE,
    mode: MODE_NAME,
    name: MODE_LABEL
  });
}

/** install the mode */
defineRobotMode();
