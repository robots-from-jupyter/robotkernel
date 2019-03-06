/*
  Copyright (c) 2018 Georgia Tech Research Corporation
  Copyright (c) 2019 Asko Soukka <asko.soukka@iki.fi>
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

/** All the possible states: pushing non-existing states == bad */
export type TMainState = 'test_cases' | 'keywords' | 'settings' | 'variables';
export type TState =
  | TMainState
  | 'double_string'
  | 'keyword_def'
  | 'keyword_invocation'
  | 'keyword_invocation_no_continue'
  | 'library'
  | 'loop_body_old'
  | 'loop_start_new'
  | 'loop_start_old'
  | 'single_string'
  | 'start'
  | 'tags'
  | 'tags_comma'
  | 'variable_index'
  | 'variable_property'
  | 'variable';

/** the tokens we use */
export enum TT {
  AM = 'atom',
  AT = 'attribute',
  BE = 'builtin.em',
  BI = 'builtin',
  BK = 'bracket',
  CM = 'comment',
  DF = 'def',
  HL = 'header',
  KW = 'keyword',
  MT = 'meta',
  NB = 'number',
  OP = 'operator',
  PC = 'punctuation',
  PR = 'property',
  SE = 'string.em',
  SH = 'string.header',
  SS = 'string.strong',
  SSE = 'string.strong.em',
  S2 = 'string-2',
  ST = 'string',
  TG = 'tag',
  V2 = 'variable-2'
}

export function LINK(token: TT): TT {
  return (token + '.link') as any;
}

/**
  An implementation of the CodeMirror simple mode object

  https://github.com/codemirror/CodeMirror/blob/master/addon/mode/simple.js
*/
interface ISimpleState {
  /** The regular expression that matches the token. May be a string or a regex object. When a regex, the ignoreCase flag will be taken into account when matching the token. This regex has to capture groups when the token property is an array. If it captures groups, it must capture all of the string (since JS provides no way to find out where a group matched). */
  regex: string | RegExp;
  /// An optional token style. Multiple styles can be specified by separating them with dots or spaces. When this property holds an array of token styles, the regex for this rule must capture a group for each array item.
  token?: TT | TT[] | null;
  /// When true, this token will only match at the start of the line. (The ^ regexp marker doesn't work as you'd expect in this context because of limitations in JavaScript's RegExp API.)
  sol?: boolean;
  /// When a next property is present, the mode will transfer to the state named by the property when the token is encountered.
  next?: TState;
  /// Like next, but instead replacing the current state by the new state, the current state is kept on a stack, and can be returned to with the pop directive.
  push?: TState;
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
export type IStates = { [key in TState]: ISimpleState[] };

/** helper function for compactly representing a rule */
function r(
  regex: RegExp,
  token?: TT | TT[],
  opt?: Partial<ISimpleState>
): ISimpleState {
  return { regex, token, ...opt };
}

/** Possible Robot Framework table names. Group count is important.  */
const TABLE_NAMES: { [key in TMainState]: RegExp } = {
  keywords: /(\|\s)?(\*+ *)(user keywords?|keywords?)( *\**)/i,
  settings: /(\|\s)?(\*+ *)(settings?)( *\**)/i,
  test_cases: /(\|\s)?(\*+ *)(tasks?|test cases?)( *\**)/i,
  variables: /(\|\s)?(\*+ *)(variables?)( *\**)/i
};

/** Enumerate the possible rules  */
const RULES_TABLE = Object.keys(TABLE_NAMES).map((next: TMainState) => {
  return r(TABLE_NAMES[next], [TT.BK, TT.HL, TT.HL, TT.HL], {
    next,
    sol: true
  });
});

const RULE_COMMENT_POP = r(/#.*$/, TT.CM, { pop: true });

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
const RULE_VAR_START = r(/[\$&@%]\{/, TT.V2, { push: 'variable' });
/** a rule for the end of the variable state */
const RULE_VAR_END = r(/\}/, TT.V2);

/** a rule for a number */
const RULE_NUM = r(VAR_NUM, TT.NB);

/** a rule for starting a single quote */
const RULE_SINGLE_STRING_START = r(/'/, TT.ST, { push: 'single_string' });
/** a rule for starting a double quote */
const RULE_DOUBLE_STRING_START = r(/"/, TT.ST, { push: 'double_string' });

/** a rule for capturing tags (and friends) in keyword/test/task definitions */
const RULE_TAGS = r(
  /([|\s]*\s*)(\[\s*)(tags)(\s*\])(\s*\|?)/i,
  [TT.BK, TT.MT, TT.MT, TT.MT, TT.BK],
  { sol: true, push: 'tags' }
);

/** rule for special case of applying tags at the suite level */
const RULE_SUITE_TAGS = r(
  /(force tags|default tags)(\t+|  +)/i,
  [TT.MT, null],
  {
    push: 'tags',
    sol: true
  }
);
/** rule for special case of applying tags at the suite level (with pipes) */
const RULE_SUITE_TAGS_PIPE = r(
  /(\| +)(force tags|default tags)( *\|?)/i,
  [TT.BK, TT.MT, TT.BK],
  { sol: true, push: 'tags' }
);

/** rule for bracketed settings of keyword/test/task */
const RULE_SETTING_KEYWORD = r(
  /([|\s]*)(\[\s*)(setup|teardown|template)(\s*\])(\s*\|?)/i,
  [TT.BK, TT.MT, TT.MT, TT.MT, TT.BK],
  { push: 'keyword_invocation_no_continue', sol: true }
);

/** rule for bracketed settings of keyword/test/task that include a keyword */
const RULE_SUITE_SETTING_KEYWORD = r(
  /(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)(\t+|  +)/i,
  [TT.MT, null],
  { push: 'keyword_invocation', sol: true }
);

/** rule for bracketed settings of keyword/test/task that include a keyword (with pipes) */
const RULE_SUITE_SETTING_KEYWORD_PIPE = r(
  /(\| +)(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)( +\|)/i,
  [TT.BK, TT.MT, TT.BK],
  { push: 'keyword_invocation', sol: true }
);

const RULE_SETTING_LIBRARY = r(/(library)(\t+|  +)/i, [TT.MT, null], {
  push: 'library',
  sol: true
});

const RULE_SETTING_LIBRARY_PIPE = r(
  /(\| +)(library)( +\|)/i,
  [TT.BK, TT.MT, TT.BK],
  {
    push: 'library',
    sol: true
  }
);

/** rule to escape the final closing bracket of a var at the end of a line */
const RULE_LINE_ENDS_WITH_VAR = r(/\}\s*(?=$)/, TT.V2, { pop: true });

const RULE_ELLIPSIS = r(/(\s*)(\.\.\.)/, [null, TT.BK], { sol: true });
const RULE_NOT_ELLIPSIS_POP = r(/(?!\s*(\\|\.\.\.))/, null, {
  pop: true,
  sol: true
});

const RULE_DOC_TAGS = r(/(Tags:)(\s*)/i, [TT.MT, null], { push: 'tags_comma' });

/** collects the states that we build */
const states: Partial<IStates> = {};

/** base isn't a state. these are the "normal business" that any state might use */
const base = [
  ...RULES_TABLE,
  RULE_VAR_START,
  RULE_VAR_END,
  RULE_DOC_TAGS,
  RULE_ELLIPSIS,
  r(/\|/, TT.BK),
  r(/#.*$/, TT.CM),
  r(/\\ +/, TT.BK),
  r(/\\(?=$)/, TT.BK),
  r(
    // a non-variable argument fragment before a variable before an equal
    /([^\s\$@&%=]((?!\t+|\s+\|\s+|  +)([^=]|\\=))*?)(?=[$@&%].*?[^ =\\]=($|  |[^=]|\s+\||\t))/,
    TT.AT
  ),
  r(
    // a non-variable argument fragment before an equal
    /([^\s\$@&%=]((?!\t+|\s+\|\s+|  +)([^=]|\\=))*?)(?==($|  |[^=]|\s+\||\t))/,
    TT.AT
  ),
  r(/[^\s]+:(?!\/)/, TT.OP),
  r(/(=!<>+\-*\/%)*==?/, TT.OP),
  r(/_\*.*?\*_/, TT.SSE),
  r(/\*.*?\*/, TT.SS),
  r(/\_.*?\_/, TT.SE),
  // this is pretty extreme, but seems to work
  r(/[^\s\$@%&]+/, TT.ST),
  r(/[\$@%&](?!\{)/, TT.ST)
];

/** the starting state (begining of a file) */
states.start = [
  r(/(%%python)( module )?(.*)?/, [TT.MT, TT.KW, TT.V2], {
    mode: { spec: 'ipython' },
    sol: true
  }),
  r(/(%%[^\s]*).*$/, TT.MT, { sol: true }),
  ...base
];

/** settings states */
states.settings = [
  RULE_SUITE_TAGS_PIPE,
  RULE_SUITE_TAGS,
  RULE_SUITE_SETTING_KEYWORD_PIPE,
  RULE_SUITE_SETTING_KEYWORD,
  RULE_SETTING_LIBRARY,
  RULE_SETTING_LIBRARY_PIPE,
  r(
    /(\|*\s*)(resource|variables|documentation|metadata|test timeout|task timeout)(\s*)/i,
    [TT.BK, TT.MT, null],
    { sol: true }
  ),
  ...base
];

states.library = [
  RULE_NOT_ELLIPSIS_POP,
  RULE_ELLIPSIS,
  RULE_LINE_ENDS_WITH_VAR,
  r(
    /(WITH NAME)(\t+|  +| +\| +)([^\|\s]*)(\s*)(\|?)(\s*)(?=$)/,
    [TT.AM, TT.BK, TT.DF, null, TT.BK, null],
    {
      pop: true
    }
  ),
  // r(/[^\}\|\s]*$/, TT.ST, { pop: true }),
  ...base
];

/** rule for behavior-driven-development keywords */
const RULE_START_BDD = r(
  /(\|\s*\|\s*|\s\s+)?(given|when|then|and|but)/i,
  [TT.BK, TT.BE],
  {
    push: 'keyword_invocation',
    sol: true
  }
);
/** rule for whitespace keywords */
const RULE_KEY_START = r(/(\t+|  +)(?!\.\.\.)/, null, {
  push: 'keyword_invocation',
  sol: true
});
/** rule for pipe keywords */
const RULE_KEY_START_PIPE = r(
  /(\| )(\s*)(|[^\|\s][^\|]*)(\s*)( \|)(\s+)/,
  [TT.BK, null, TT.SH, null, TT.BK, null],
  {
    push: 'keyword_invocation',
    sol: true
  }
);
/** rule for for old-style loops (slashes) */
const RULE_START_LOOP_OLD = r(
  /(\s\|*\s*)(:FOR)(\s\|*\s*)/,
  [null, TT.AM, null],
  {
    push: 'loop_start_old',
    sol: true
  }
);
/** rule for for new-style loops (slashes) */
const RULE_START_LOOP_NEW = r(
  /(\s\|*\s*)(FOR)(\s\|*\s*)/,
  [null, TT.AM, null],
  {
    push: 'loop_start_new',
    sol: true
  }
);

const RULES_TAGS_COMMON = [
  r(/\s\|\s*/, TT.BK),
  RULE_COMMENT_POP,
  RULE_ELLIPSIS,
  RULE_NOT_ELLIPSIS_POP,
  RULE_VAR_START,
  RULE_LINE_ENDS_WITH_VAR,
  RULE_VAR_END,
  r(/ +/, null)
];

/** rules for capturing individual tags */
states.tags = [
  ...RULES_TAGS_COMMON,
  r(/[^\$&%@]*?(?=(  +| \|))/, TT.TG),
  // fall back to single char
  r(/[^\$&%@|]/, TT.TG)
];

/** rules for capturing tags inside docs */
states.tags_comma = [
  ...RULES_TAGS_COMMON,
  r(/(,)(\s*)/, [TT.PC, null]),
  r(/[^\$&%@,]+(?=,$)/, TT.TG),
  // fall back to single char
  r(/[^\$&%@|,]/, TT.TG)
];

/** need to catch empty white lines pretty explicitly */
const RULE_WS_LINE = r(/\s*(?=$)/, null, { sol: true });

/** not a state. rules for starting keyword invocation */
const RULES_KEYWORD_INVOKING = [
  RULE_START_BDD,
  RULE_KEY_START_PIPE,
  RULE_KEY_START,
  r(/\|\s(?=[^\s*]*\|)/, null, { sol: true, push: 'keyword_invocation' }),
  r(/(?=[^\s*])/, null, { sol: true, push: 'keyword_invocation' })
];

const RULE_SETTING_SIMPLE = r(
  /(\t+|  +)(\[\s*)(arguments|documentation|return|timeout)(\s*\])(\s*)/i,
  [null, TT.MT, TT.MT, TT.MT, null],
  { sol: true }
);

const RULE_SETTING_SIMPLE_PIPE = r(
  /(\|)(\s+)([^|*]*)(\s+)(\|)(\s+)(\[\s*)(arguments|documentation|return|timeout)(\s*\])(\s*)(\|?)/i,
  [TT.BK, null, TT.SH, null, TT.BK, null, TT.MT, TT.MT, TT.MT, null, TT.BK],
  { sol: true }
);

/** rules for data rows inside a keyword table */
states.keywords = [
  RULE_ELLIPSIS,
  RULE_TAGS,
  RULE_SETTING_KEYWORD,
  RULE_SETTING_SIMPLE,
  RULE_SETTING_SIMPLE_PIPE,
  r(/(?=[^\s$&%@*|]+)/, null, { sol: true, push: 'keyword_def' }),
  RULE_START_LOOP_OLD,
  RULE_START_LOOP_NEW,
  RULE_WS_LINE,
  ...RULES_KEYWORD_INVOKING,
  ...base
];

/** a keyword name fragment before an inline variable */
const KEYWORD_WORD_BEFORE_VAR = /([^\s]*?(?=[\$&%@]\{))/i;
/** a keyword name fragment before a separator */
const KEYWORD_WORD_BEFORE_SEP = /[^\s\|]+(?=$|[|]|\t|  +)/;
/** a keyword name fragment before a non-separator whitespace character */
const KEYWORD_WORD_BEFORE_WS = /([^\n\$\s*=\|]+?(?= ))/i;

states.keyword_def = [
  RULE_VAR_START,
  RULE_LINE_ENDS_WITH_VAR,
  RULE_VAR_END,
  r(/ /, null),
  r(KEYWORD_WORD_BEFORE_VAR, TT.DF),
  r(KEYWORD_WORD_BEFORE_SEP, TT.DF, { pop: true }),
  r(KEYWORD_WORD_BEFORE_WS, TT.DF),
  r(/(?=$)/, null, { sol: true, pop: true })
];

/** A range as used in for loops */
const RULE_RANGE = r(/([\|\s]*\s*)(IN)( RANGE| ENUMERATE| ZIP)?/, [
  null,
  TT.AM,
  TT.AM
]);

states.loop_start_new = [
  RULE_RANGE,
  r(/[.]{3}/, TT.BK),
  RULE_VAR_START,
  r(/\}(?=$)/, TT.V2),
  RULE_VAR_END,
  r(/([\|\s]*\s*)(END)/, [null, TT.AM], { sol: true, pop: true }),
  RULE_WS_LINE,
  ...RULES_KEYWORD_INVOKING,
  ...base
];

states.loop_start_old = [
  r(/(?=.*)/, null, { sol: true, next: 'loop_body_old' }),
  RULE_RANGE,
  RULE_VAR_START,
  r(/\}(?=$)/, TT.V2),
  RULE_VAR_END,
  ...base
];

states.loop_body_old = [
  ...RULES_KEYWORD_INVOKING.map(rule => {
    return {
      ...rule,
      regex: new RegExp(
        /([\|\s]*\s*)(\\)/.source +
          (rule.regex instanceof RegExp ? rule.regex.source : rule.regex)
      ),
      token:
        rule.token instanceof Array
          ? [null, TT.BK, ...rule.token]
          : [null, TT.BK, rule.token]
    };
  }),
  r(/(?=\s+[^\\])/, null, { pop: true, sol: true }),
  ...base
];

const RULE_CASE_SETTING_SIMPLE = r(
  /(\t+|  +)(\[\s*)(documentation|timeout)(\s*\])(\s*)/i,
  [null, TT.MT, TT.MT, TT.MT, null],
  { sol: true }
);

const RULE_CASE_SETTING_SIMPLE_PIPE = r(
  /(\|)(\s+)([^|*]*)(\s+)(\|)(\s+)(\[\s*)(documentation|timeout)(\s*\])(\s*)(\|?)/i,
  [TT.BK, null, TT.SH, null, TT.BK, null, TT.MT, TT.MT, TT.MT, null, TT.BK],
  { sol: true }
);

/** rules for data rows inside test/task definition */
states.test_cases = [
  ...RULES_TABLE,
  RULE_WS_LINE,
  RULE_ELLIPSIS,
  RULE_TAGS,
  RULE_SETTING_KEYWORD,
  RULE_CASE_SETTING_SIMPLE,
  RULE_CASE_SETTING_SIMPLE_PIPE,
  RULE_START_LOOP_OLD,
  RULE_START_LOOP_NEW,
  r(/([^|\s*].+?)(?=(\t|  +|$))/, TT.SH, { sol: true }),
  ...RULES_KEYWORD_INVOKING,
  r(/(\|\s+)([^\s*\|\.][^\|]*?)(\s*)(\|?$)/, [TT.BK, TT.SH, TT.BK], {
    sol: true
  }),
  r(/(\| +)([^\|\s].+?)(\s*)( \| )/, [TT.BK, TT.SH, null, TT.BK], {
    sol: true
  }),
  ...base
];

/** rules for inside of an invoked keyword instance */
states.keyword_invocation = [
  r(/( ?)(=)(\t+|  +|\s+\|)/, [null, TT.OP, null]),
  r(/(?=\s*$)/, null, { pop: true }),
  r(/(\\|\.\.\.) +/, TT.BK, { pop: true }),
  RULE_VAR_START,
  RULE_LINE_ENDS_WITH_VAR,
  RULE_VAR_END,
  RULE_COMMENT_POP,
  r(/( \| |  +|\t+)(?=[$@&])/, TT.BK),
  r(/( \| |  +|\t+)/, TT.BK, { pop: true }),
  r(/ /, null),
  r(KEYWORD_WORD_BEFORE_VAR, TT.KW, { pop: true }),
  r(KEYWORD_WORD_BEFORE_SEP, TT.KW, { pop: true }),
  r(KEYWORD_WORD_BEFORE_WS, TT.KW),
  ...base
];

states.keyword_invocation_no_continue = [
  RULE_NOT_ELLIPSIS_POP,
  ...states.keyword_invocation
];

/** curious rule for the variables table */
states.variables = [...base];

/** rules for inside of a variable reference */
states.variable = [
  RULE_VAR_START,
  r(VAR_BUILTIN, TT.BI),
  RULE_NUM,
  r(VAR_OP, TT.OP),
  r(/(:)(.*?[^\\])(?=\}\s*$)/, [TT.OP, TT.S2], { pop: true }),
  r(/(:)(.*?[^\\])(?=\})/, [TT.OP, TT.S2]),
  r(/\./, TT.OP, { push: 'variable_property' }),
  r(/\[/, TT.BK, { next: 'variable_index' }),
  r(/\}(?=\[)/, TT.V2),
  r(/(?=\}\s*$)/, null, { pop: true }),
  r(/\}/, TT.V2, { pop: true }),
  r(/[^\{\}\n:]/, TT.V2)
];

/** rules for extended syntax in a variable reference */
states.variable_property = [
  RULE_VAR_START,
  RULE_VAR_END,
  RULE_NUM,
  RULE_SINGLE_STRING_START,
  RULE_DOUBLE_STRING_START,
  r(VAR_OP, TT.OP),
  r(/\(/, TT.BK),
  r(/\)/, TT.BK, { pop: true }),
  r(/([a-z_][a-z_\d]*)(=)/i, [TT.V2, TT.OP]),
  r(/,/, TT.PC),
  r(/[^}](?=\})/, TT.PR, { pop: true }),
  r(/(\})(\s*(?=$|\n))/, [TT.BK, null], { pop: true }),
  r(/\t*(?=$|\n)/, null, { pop: true }),
  r(/[^}]/, TT.PR)
];

/** rules for strings with single quotes */
states.single_string = [
  r(/\\'/, TT.ST),
  r(/'/, TT.ST, { pop: true }),
  r(/./, TT.ST)
];
/** rules for strings with double quotes */
states.double_string = [
  r(/\\"/, TT.ST),
  r(/"/, TT.ST, { pop: true }),
  r(/./, TT.ST)
];

/** rules for square-bracketed index referencing */
states.variable_index = [
  RULE_VAR_START,
  RULE_VAR_END,
  RULE_NUM,
  r(/\[/, TT.BK),
  r(/\](?=\])/, TT.BK),
  r(/(\])(\})( ?=?)/, [TT.BK, TT.V2, TT.OP], { pop: true }),
  r(/(\])(\[)/, TT.BK),
  r(/\]/, TT.BK, { pop: true }),
  r(/[^\]]/, TT.ST)
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
