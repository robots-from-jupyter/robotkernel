(function() {

"use strict";

// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

CodeMirror.defineSimpleMode = function(name, states) {
  CodeMirror.defineMode(name, function(config) {
    return CodeMirror.simpleMode(config, states);
  });
};

CodeMirror.simpleMode = function(config, states) {
  ensureState(states, "start");
  var states_ = {}, meta = states.meta || {}, hasIndentation = false;
  for (var state in states) if (state != meta && states.hasOwnProperty(state)) {
    var list = states_[state] = [], orig = states[state];
    for (var i = 0; i < orig.length; i++) {
      var data = orig[i];
      list.push(new Rule(data, states));
      if (data.indent || data.dedent) hasIndentation = true;
    }
  }
  var mode = {
    startState: function() {
      return {state: "start", pending: null,
              local: null, localState: null,
              indent: hasIndentation ? [] : null};
    },
    copyState: function(state) {
      var s = {state: state.state, pending: state.pending,
               local: state.local, localState: null,
               indent: state.indent && state.indent.slice(0)};
      if (state.localState)
        s.localState = CodeMirror.copyState(state.local.mode, state.localState);
      if (state.stack)
        s.stack = state.stack.slice(0);
      for (var pers = state.persistentStates; pers; pers = pers.next)
        s.persistentStates = {mode: pers.mode,
                              spec: pers.spec,
                              state: pers.state == state.localState ? s.localState : CodeMirror.copyState(pers.mode, pers.state),
                              next: s.persistentStates};
      return s;
    },
    token: tokenFunction(states_, config),
    innerMode: function(state) { return state.local && {mode: state.local.mode, state: state.localState}; },
    indent: indentFunction(states_, meta)
  };
  if (meta) for (var prop in meta) if (meta.hasOwnProperty(prop))
    mode[prop] = meta[prop];
  return mode;
};

function ensureState(states, name) {
  if (!states.hasOwnProperty(name))
    throw new Error("Undefined state " + name + " in simple mode");
}

function toRegex(val, caret) {
  if (!val) return /(?:)/;
  var flags = "";
  if (val instanceof RegExp) {
    if (val.ignoreCase) flags = "i";
    val = val.source;
  } else {
    val = String(val);
  }
  return new RegExp((caret === false ? "" : "^") + "(?:" + val + ")", flags);
}

function asToken(val) {
  if (!val) return null;
  if (val.apply) return val
  if (typeof val == "string") return val.replace(/\./g, " ");
  var result = [];
  for (var i = 0; i < val.length; i++)
    result.push(val[i] && val[i].replace(/\./g, " "));
  return result;
}

function Rule(data, states) {
  if (data.next || data.push) ensureState(states, data.next || data.push);
  this.regex = toRegex(data.regex);
  this.token = asToken(data.token);
  this.data = data;
}

function tokenFunction(states, config) {
  return function(stream, state) {
    if (state.pending) {
      var pend = state.pending.shift();
      if (state.pending.length == 0) state.pending = null;
      stream.pos += pend.text.length;
      return pend.token;
    }

    if (state.local) {
      if (state.local.end && stream.match(state.local.end)) {
        var tok = state.local.endToken || null;
        state.local = state.localState = null;
        return tok;
      } else {
        var tok = state.local.mode.token(stream, state.localState), m;
        if (state.local.endScan && (m = state.local.endScan.exec(stream.current())))
          stream.pos = stream.start + m.index;
        return tok;
      }
    }

    var curState = states[state.state];
    for (var i = 0; i < curState.length; i++) {
      var rule = curState[i];
      var matches = (!rule.data.sol || stream.sol()) && stream.match(rule.regex);
      if (matches) {
        if (rule.data.next) {
          state.state = rule.data.next;
        } else if (rule.data.push) {
          (state.stack || (state.stack = [])).push(state.state);
          state.state = rule.data.push;
        } else if (rule.data.pop && state.stack && state.stack.length) {
          state.state = state.stack.pop();
        }

        if (rule.data.mode)
          enterLocalMode(config, state, rule.data.mode, rule.token);
        if (rule.data.indent)
          state.indent.push(stream.indentation() + config.indentUnit);
        if (rule.data.dedent)
          state.indent.pop();
        var token = rule.token
        if (token && token.apply) token = token(matches)
        if (matches.length > 2 && rule.token && typeof rule.token != "string") {
          state.pending = [];
          for (var j = 2; j < matches.length; j++)
            if (matches[j])
              state.pending.push({text: matches[j], token: rule.token[j - 1]});
          stream.backUp(matches[0].length - (matches[1] ? matches[1].length : 0));
          return token[0];
        } else if (token && token.join) {
          return token[0];
        } else {
          return token;
        }
      }
    }
    stream.next();
    return null;
  };
}

function cmp(a, b) {
  if (a === b) return true;
  if (!a || typeof a != "object" || !b || typeof b != "object") return false;
  var props = 0;
  for (var prop in a) if (a.hasOwnProperty(prop)) {
    if (!b.hasOwnProperty(prop) || !cmp(a[prop], b[prop])) return false;
    props++;
  }
  for (var prop in b) if (b.hasOwnProperty(prop)) props--;
  return props == 0;
}

function enterLocalMode(config, state, spec, token) {
  var pers;
  if (spec.persistent) for (var p = state.persistentStates; p && !pers; p = p.next)
    if (spec.spec ? cmp(spec.spec, p.spec) : spec.mode == p.mode) pers = p;
  var mode = pers ? pers.mode : spec.mode || CodeMirror.getMode(config, spec.spec);
  var lState = pers ? pers.state : CodeMirror.startState(mode);
  if (spec.persistent && !pers)
    state.persistentStates = {mode: mode, spec: spec.spec, state: lState, next: state.persistentStates};

  state.localState = lState;
  state.local = {mode: mode,
                 end: spec.end && toRegex(spec.end),
                 endScan: spec.end && spec.forceEnd !== false && toRegex(spec.end, false),
                 endToken: token && token.join ? token[token.length - 1] : token};
}

function indexOf(val, arr) {
  for (var i = 0; i < arr.length; i++) if (arr[i] === val) return true;
}

function indentFunction(states, meta) {
  return function(state, textAfter, line) {
    if (state.local && state.local.mode.indent)
      return state.local.mode.indent(state.localState, textAfter, line);
    if (state.indent == null || state.local || meta.dontIndentStates && indexOf(state.state, meta.dontIndentStates) > -1)
      return CodeMirror.Pass;

    var pos = state.indent.length - 1, rules = states[state.state];
    scan: for (;;) {
      for (var i = 0; i < rules.length; i++) {
        var rule = rules[i];
        if (rule.data.dedent && rule.data.dedentIfLineStart !== false) {
          var m = rule.regex.exec(textAfter);
          if (m && m[0]) {
            pos--;
            if (rule.next || rule.push) rules = states[rule.next || rule.push];
            textAfter = textAfter.slice(m[0].length);
            continue scan;
          }
        }
      }
      break;
    }
    return pos < 0 ? 0 : state.indent[pos];
  };
}

/*
  Copyright (c) 2018 Georgia Tech Research Corporation
  Copyright (c) 2019 Asko Soukka <asko.soukka@iki.fi>
  Distributed under the terms of the BSD-3-Clause License
*/
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
/*
  Copyright (c) 2022 MarketSquare
  Distributed under the terms of the BSD-3-Clause License
*/
/** the tokens we use */
var TT;
(function (TT) {
    TT["AM"] = "atom";
    TT["AT"] = "attribute";
    TT["BE"] = "builtin.em";
    TT["BI"] = "builtin";
    TT["BK"] = "bracket";
    TT["CM"] = "comment";
    TT["DF"] = "def";
    TT["HL"] = "header";
    TT["KW"] = "keyword";
    TT["MT"] = "meta";
    TT["NB"] = "number";
    TT["OP"] = "operator";
    TT["PC"] = "punctuation";
    TT["PR"] = "property";
    TT["SE"] = "string.em";
    TT["SH"] = "string.header";
    TT["SS"] = "string.strong";
    TT["SSE"] = "string.strong.em";
    TT["S2"] = "string-2";
    TT["ST"] = "string";
    TT["TG"] = "tag";
    TT["V2"] = "variable-2";
})(TT || (TT = {}));
/** helper function for compactly representing a rule */
function r(regex, token, opt) {
    return { regex, token, ...opt };
}
/** Possible Robot Framework table names. Group count is important.  */
const TABLE_NAMES = {
    keywords: /(\|\s)?(\*+ *)(user keywords?|keywords?)( *\**)/i,
    settings: /(\|\s)?(\*+ *)(settings?)( *\**)/i,
    test_cases: /(\|\s)?(\*+ *)(tasks?|test cases?)( *\**)/i,
    variables: /(\|\s)?(\*+ *)(variables?)( *\**)/i,
};
/** Enumerate the possible rules  */
const RULES_TABLE = Object.keys(TABLE_NAMES).map((next) => {
    return r(TABLE_NAMES[next], [TT.BK, TT.HL, TT.HL, TT.HL], {
        next,
        sol: true,
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
const RULE_TAGS = r(/([|\s]*\s*)(\[\s*)(tags)(\s*\])(\s*\|?)/i, [TT.BK, TT.MT, TT.MT, TT.MT, TT.BK], { sol: true, push: 'tags' });
/** rule for special case of applying tags at the suite level */
const RULE_SUITE_TAGS = r(/(force tags|default tags)(\t+|  +)/i, [TT.MT, null], {
    push: 'tags',
    sol: true,
});
/** rule for special case of applying tags at the suite level (with pipes) */
const RULE_SUITE_TAGS_PIPE = r(/(\| +)(force tags|default tags)( *\|?)/i, [TT.BK, TT.MT, TT.BK], { sol: true, push: 'tags' });
/** rule for bracketed settings of keyword/test/task */
const RULE_SETTING_KEYWORD = r(/([|\s]*)(\[\s*)(setup|teardown|template)(\s*\])(\s*\|?)/i, [TT.BK, TT.MT, TT.MT, TT.MT, TT.BK], { push: 'keyword_invocation_no_continue', sol: true });
/** rule for bracketed settings of keyword/test/task that include a keyword */
const RULE_SUITE_SETTING_KEYWORD = r(/(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)(\t+|  +)/i, [TT.MT, null], { push: 'keyword_invocation', sol: true });
/** rule for bracketed settings of keyword/test/task that include a keyword (with pipes) */
const RULE_SUITE_SETTING_KEYWORD_PIPE = r(/(\| +)(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)( +\|)/i, [TT.BK, TT.MT, TT.BK], { push: 'keyword_invocation', sol: true });
const RULE_SETTING_LIBRARY = r(/(library)(\t+|  +)/i, [TT.MT, null], {
    push: 'library',
    sol: true,
});
const RULE_SETTING_LIBRARY_PIPE = r(/(\| +)(library)( +\|)/i, [TT.BK, TT.MT, TT.BK], {
    push: 'library',
    sol: true,
});
/** rule to escape the final closing bracket of a var at the end of a line */
const RULE_LINE_ENDS_WITH_VAR = r(/\}\s*(?=$)/, TT.V2, { pop: true });
const RULE_ELLIPSIS = r(/(\s*)(\.\.\.)/, [null, TT.BK], { sol: true });
const RULE_NOT_ELLIPSIS_POP = r(/(?!\s*(\\|\.\.\.))/, null, {
    pop: true,
    sol: true,
});
const RULE_DOC_TAGS = r(/(Tags:)(\s*)/i, [TT.MT, null], { push: 'tags_comma' });
/** collects the states that we build */
const states = {};
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
    /([^\s\$@&%=]((?!\t+|\s+\|\s+|  +)([^=]|\\=))*?)(?=[$@&%].*?[^ =\\]=($|  |[^=]|\s+\||\t))/, TT.AT),
    r(
    // a non-variable argument fragment before an equal
    /([^\s\$@&%=]((?!\t+|\s+\|\s+|  +)([^=]|\\=))*?)(?==($|  |[^=]|\s+\||\t))/, TT.AT),
    // r(/[^\s]+:(?!\/)/, TT.OP),  // this was generating false positives with TRY
    r(/(=!<>+\-*\/%)*==?/, TT.OP),
    r(/_\*.*?\*_/, TT.SSE),
    r(/\*.*?\*/, TT.SS),
    r(/\_.*?\_/, TT.SE),
    // this is pretty extreme, but seems to work
    r(/[^\s\$@%&]+/, TT.ST),
    r(/[\$@%&](?!\{)/, TT.ST),
];
/** the starting state (begining of a file) */
states.start = [
    r(/(%%python)( module )?(.*)?/, [TT.MT, TT.KW, TT.V2], {
        mode: { spec: 'ipython' },
        sol: true,
    }),
    r(/(%%[^\s]*).*$/, TT.MT, { sol: true }),
    ...base,
];
/** settings states */
states.settings = [
    RULE_SUITE_TAGS_PIPE,
    RULE_SUITE_TAGS,
    RULE_SUITE_SETTING_KEYWORD_PIPE,
    RULE_SUITE_SETTING_KEYWORD,
    RULE_SETTING_LIBRARY,
    RULE_SETTING_LIBRARY_PIPE,
    r(/(\|*\s*)(resource|variables|documentation|metadata|test timeout|task timeout)(\s*)/i, [TT.BK, TT.MT, null], { sol: true }),
    ...base,
];
states.library = [
    RULE_NOT_ELLIPSIS_POP,
    RULE_ELLIPSIS,
    RULE_LINE_ENDS_WITH_VAR,
    r(/(WITH NAME)(\t+|  +| +\| +)([^\|\s]*)(\s*)(\|?)(\s*)(?=$)/, [TT.AM, TT.BK, TT.DF, null, TT.BK, null], {
        pop: true,
    }),
    ...base,
];
/** rule for behavior-driven-development keywords */
const RULE_START_BDD = r(/(\|\s*\|\s*|\s\s+)?(given|when|then|and|but)/i, [TT.BK, TT.BE], {
    push: 'keyword_invocation',
    sol: true,
});
/** rule for whitespace keywords */
const RULE_KEY_START = r(/(\t+|  +)(?!\.\.\.)/, null, {
    push: 'keyword_invocation',
    sol: true,
});
/** rule for pipe keywords */
const RULE_KEY_START_PIPE = r(/(\| )(\s*)(|[^\|\s][^\|]*)(\s*)( \|)(\s+)/, [TT.BK, null, TT.SH, null, TT.BK, null], {
    push: 'keyword_invocation',
    sol: true,
});
/** rule for for old-style loops (slashes) */
const RULE_START_LOOP_OLD = r(/(\s\|*\s*)(:FOR)(\s\|*\s*)/, [null, TT.AM, null], {
    push: 'loop_start_old',
    sol: true,
});
/** rule for for new-style loops (slashes) */
const RULE_START_LOOP_NEW = r(/(\s\|*\s*)(FOR)(\s\|*\s*)/, [null, TT.AM, null], {
    push: 'loop_start_new',
    sol: true,
});
/** rule for inline if keyword */
const RULE_START_INLINE_IF = r(/(\s*)(IF)(\s\|*\s*)(?=[^\s].*\s{2,})/, [null, TT.AM, null], { push: 'inline_if_start', sol: true });
/** rule for inline if keyword with assignment */
const RULE_START_INLINE_IF_VAR = r(/(\s+)(.*?)(\s+)(=)(\s+)(IF)(\s\|*\s*)(?=[^\s].*\s{2,})/, [null, TT.V2, null, TT.OP, null, TT.AM, null], { push: 'inline_if_start', sol: true });
/** rule for if keyword */
const RULE_START_IF = r(/(\s\|*\s*)(IF)(\s\|*\s*)(?![^\s].*\s{2,})/, [null, TT.AM, null], {
    push: 'if_start',
    sol: true,
});
/** rule for else if keyword */
const RULE_START_IF_ELSE_IF = r(/(\s\|*\s*)(ELSE IF)(\s\|*\s*)/, [null, TT.AM, null], {
    next: 'if_else_if_start',
    sol: true,
});
/** rule for else keyword */
const RULE_START_IF_ELSE = r(/(\s\|*\s*)(ELSE)(?=$)/, [null, TT.AM], {
    next: 'if_else_start',
    sol: true,
});
/** rule for try keyword */
const RULE_START_TRY = r(/(\s\|*\s*)(TRY)(?=$)/, [null, TT.AM], {
    push: 'try_start',
    sol: true,
});
/** rule for simple try/except */
const RULE_START_EXCEPT = r(/(\s\|*\s*)(EXCEPT)/, [null, TT.AM], {
    next: 'try_except_start',
    sol: true,
});
/** rule for try/else keyword */
const RULE_START_TRY_ELSE = r(/(\s\|*\s*)(ELSE)(?=$)/, [null, TT.AM], {
    next: 'try_else_start',
    sol: true,
});
/** rule for try/finally keyword */
const RULE_START_FINALLY = r(/(\s\|*\s*)(FINALLY)/, [null, TT.AM], {
    next: 'try_finally_start',
    sol: true,
});
const RULE_START_WHILE = r(/(\s\|*\s*)(WHILE)/, [null, TT.AM], {
    push: 'while_start',
    sol: true,
});
/** rule for end keyword */
const RULE_END = r(/([\|\s]*\s*)(END)(?=$)/, [null, TT.AM], {
    sol: true,
    pop: true,
});
const RULES_TAGS_COMMON = [
    r(/\s\|\s*/, TT.BK),
    RULE_COMMENT_POP,
    RULE_ELLIPSIS,
    RULE_NOT_ELLIPSIS_POP,
    RULE_VAR_START,
    RULE_LINE_ENDS_WITH_VAR,
    RULE_VAR_END,
    r(/ +/, null),
];
/** rules for capturing individual tags */
states.tags = [
    ...RULES_TAGS_COMMON,
    r(/[^\$&%@]*?(?=(  +| \|))/, TT.TG),
    // fall back to single char
    r(/[^\$&%@|]/, TT.TG),
];
/** rules for capturing tags inside docs */
states.tags_comma = [
    ...RULES_TAGS_COMMON,
    r(/(,)(\s*)/, [TT.PC, null]),
    r(/[^\$&%@,]+(?=,$)/, TT.TG),
    // fall back to single char
    r(/[^\$&%@|,]/, TT.TG),
];
/** need to catch empty white lines pretty explicitly */
const RULE_WS_LINE = r(/\s*(?=$)/, null, { sol: true });
/** not a state. rules for starting keyword invocation */
const RULES_KEYWORD_INVOKING = [
    RULE_START_BDD,
    RULE_KEY_START_PIPE,
    RULE_KEY_START,
    r(/\|\s(?=[^\s*]*\|)/, null, { sol: true, push: 'keyword_invocation' }),
    r(/(?=[^\s*])/, null, { sol: true, push: 'keyword_invocation' }),
];
const RULE_SETTING_SIMPLE = r(/(\t+|  +)(\[\s*)(arguments|documentation|return|timeout)(\s*\])(\s*)/i, [null, TT.MT, TT.MT, TT.MT, null], { sol: true });
const RULE_SETTING_SIMPLE_PIPE = r(/(\|)(\s+)([^|*]*)(\s+)(\|)(\s+)(\[\s*)(arguments|documentation|return|timeout)(\s*\])(\s*)(\|?)/i, [TT.BK, null, TT.SH, null, TT.BK, null, TT.MT, TT.MT, TT.MT, null, TT.BK], { sol: true });
/** rule for atomic control flow */
const RULE_CONTROL_FLOW_ATOM = r(/(\s*)(BREAK|CONTINUE|RETURN)([\s\|]{2,}|$)/, [
    null,
    TT.AM,
    null,
]);
/** rules for starting control flow blocks */
const RULES_CONTROL_FLOW = [
    RULE_CONTROL_FLOW_ATOM,
    RULE_START_LOOP_OLD,
    RULE_START_LOOP_NEW,
    RULE_START_WHILE,
    RULE_START_INLINE_IF_VAR,
    RULE_START_INLINE_IF,
    RULE_START_IF,
    RULE_START_TRY,
];
/** rules for data rows inside a keyword table */
states.keywords = [
    RULE_ELLIPSIS,
    RULE_TAGS,
    RULE_SETTING_KEYWORD,
    RULE_SETTING_SIMPLE,
    RULE_SETTING_SIMPLE_PIPE,
    r(/(?=[^\s$&%@*|]+)/, null, { sol: true, push: 'keyword_def' }),
    ...RULES_CONTROL_FLOW,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
/** a keyword name fragment before an inline variable */
const KEYWORD_WORD_BEFORE_VAR = /([^\s]*?(?=[\$&%@]\{))/i;
/** a keyword containing spaces before a separator */
const KEYWORD_WORD_WITH_SPACES_BEFORE_SEP = /(?:[^\t\n\r\|])+?(?=$|\t|\n|\r|  +)/;
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
    r(/(?=$)/, null, { sol: true, pop: true }),
];
/** A range as used in for loops */
const RULE_RANGE = r(/([\|\s]*\s*)(IN)( RANGE| ENUMERATE| ZIP)?/, [null, TT.AM, TT.AM]);
states.loop_start_new = [
    RULE_RANGE,
    r(/[.]{3}/, TT.BK),
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...RULES_CONTROL_FLOW,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
/** the state when in an (ELSE)IF predictate */
states.inline_if_start = [
    RULE_ELLIPSIS,
    r(/[\s\|]{2,}/, null, { next: 'inline_if_start_keyword' }),
    RULE_NOT_ELLIPSIS_POP,
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...base,
];
/** the state when in an ELSE( IF) object */
states.inline_if_start_keyword = [
    RULE_ELLIPSIS,
    RULE_CONTROL_FLOW_ATOM,
    RULE_NOT_ELLIPSIS_POP,
    r(KEYWORD_WORD_BEFORE_VAR, TT.KW, { next: 'inline_if_keyword_invoking' }),
    r(KEYWORD_WORD_WITH_SPACES_BEFORE_SEP, TT.KW, { next: 'inline_if_keyword_invoking' }),
    r(KEYWORD_WORD_BEFORE_SEP, TT.KW, { next: 'inline_if_keyword_invoking' }),
    r(KEYWORD_WORD_BEFORE_WS, TT.KW, { next: 'inline_if_keyword_invoking' }),
];
/** the state when in an ELSE( IF) object */
states.inline_if_keyword_invoking = [
    RULE_ELLIPSIS,
    RULE_NOT_ELLIPSIS_POP,
    r(/(\s\|*\s*)(ELSE IF)(\s\|*\s*)/, [null, TT.AM, null], { next: 'inline_if_start' }),
    r(/(\s\|*\s*)(ELSE)(\s\|*\s*)/, [null, TT.AM, null], {
        next: 'inline_if_start_else',
    }),
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...base,
];
states.inline_if_start_else = [
    RULE_ELLIPSIS,
    r(KEYWORD_WORD_BEFORE_VAR, TT.KW, { next: 'inline_if_else_keyword_invoking' }),
    r(KEYWORD_WORD_WITH_SPACES_BEFORE_SEP, TT.KW, {
        next: 'inline_if_else_keyword_invoking',
    }),
    r(KEYWORD_WORD_BEFORE_SEP, TT.KW, { next: 'inline_if_else_keyword_invoking' }),
    r(KEYWORD_WORD_BEFORE_WS, TT.KW, { next: 'inline_if_else_keyword_invoking' }),
    ...base,
];
states.inline_if_else_keyword_invoking = [
    RULE_ELLIPSIS,
    RULE_NOT_ELLIPSIS_POP,
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...base,
];
states.if_start = [
    r(/[.]{3}/, TT.BK),
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...RULES_CONTROL_FLOW,
    RULE_START_IF_ELSE_IF,
    RULE_START_IF_ELSE,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.if_else_if_start = [
    r(/[.]{3}/, TT.BK),
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...RULES_CONTROL_FLOW,
    RULE_START_IF_ELSE_IF,
    RULE_START_IF_ELSE,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.if_else_start = [
    ...RULES_CONTROL_FLOW,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.try_start = [
    ...RULES_CONTROL_FLOW,
    RULE_START_EXCEPT,
    RULE_START_TRY_ELSE,
    RULE_START_FINALLY,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.try_except_start = [
    r(/[.]{3}/, TT.BK),
    r(/AS/, TT.AM),
    r(/(glob|regexp):/i, TT.BI),
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...RULES_CONTROL_FLOW,
    RULE_START_EXCEPT,
    RULE_START_TRY_ELSE,
    RULE_START_FINALLY,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.try_else_start = [
    ...RULES_CONTROL_FLOW,
    RULE_START_FINALLY,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.try_finally_start = [
    ...RULES_CONTROL_FLOW,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.while_start = [
    r(/[.]{3}/, TT.BK),
    r(/AS/, TT.AM),
    r(/(glob|regexp):/i, TT.BI),
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...RULES_CONTROL_FLOW,
    RULE_END,
    RULE_WS_LINE,
    ...RULES_KEYWORD_INVOKING,
    ...base,
];
states.loop_start_old = [
    r(/(?=.*)/, null, { sol: true, next: 'loop_body_old' }),
    RULE_RANGE,
    RULE_VAR_START,
    r(/\}(?=$)/, TT.V2),
    RULE_VAR_END,
    ...base,
];
states.loop_body_old = [
    ...RULES_KEYWORD_INVOKING.map((rule) => {
        return {
            ...rule,
            regex: new RegExp(/([\|\s]*\s*)(\\)/.source +
                (rule.regex instanceof RegExp ? rule.regex.source : rule.regex)),
            token: rule.token instanceof Array
                ? [null, TT.BK, ...rule.token]
                : [null, TT.BK, rule.token],
        };
    }),
    r(/(?=\s+[^\\])/, null, { pop: true, sol: true }),
    ...base,
];
const RULE_CASE_SETTING_SIMPLE = r(/(\t+|  +)(\[\s*)(documentation|timeout)(\s*\])(\s*)/i, [null, TT.MT, TT.MT, TT.MT, null], { sol: true });
const RULE_CASE_SETTING_SIMPLE_PIPE = r(/(\|)(\s+)([^|*]*)(\s+)(\|)(\s+)(\[\s*)(documentation|timeout)(\s*\])(\s*)(\|?)/i, [TT.BK, null, TT.SH, null, TT.BK, null, TT.MT, TT.MT, TT.MT, null, TT.BK], { sol: true });
/** rules for data rows inside test/task definition */
states.test_cases = [
    ...RULES_TABLE,
    RULE_WS_LINE,
    RULE_ELLIPSIS,
    RULE_TAGS,
    RULE_SETTING_KEYWORD,
    RULE_CASE_SETTING_SIMPLE,
    RULE_CASE_SETTING_SIMPLE_PIPE,
    ...RULES_CONTROL_FLOW,
    r(/([^|\s*].+?)(?=(\t|  +|$))/, TT.SH, { sol: true }),
    ...RULES_KEYWORD_INVOKING,
    r(/(\|\s+)([^\s*\|\.][^\|]*?)(\s*)(\|?$)/, [TT.BK, TT.SH, TT.BK], {
        sol: true,
    }),
    r(/(\| +)([^\|\s].+?)(\s*)( \| )/, [TT.BK, TT.SH, null, TT.BK], {
        sol: true,
    }),
    ...base,
];
/** rules for inside of an invoked keyword instance */
states.keyword_invocation = [
    r(/( ?)(=)(\t+|  +|\s+\|)/, [null, TT.OP, null]),
    r(/(?=\s*$)/, null, { pop: true }),
    r(/(\\|\.\.\.) +/, TT.BK),
    RULE_VAR_START,
    RULE_LINE_ENDS_WITH_VAR,
    RULE_VAR_END,
    RULE_COMMENT_POP,
    r(/( \| |  +|\t+)(?=[$@&])/, TT.BK),
    r(/( \| |  +|\t+)/, TT.BK, { pop: true }),
    r(/ /, null),
    r(KEYWORD_WORD_BEFORE_VAR, TT.KW, { pop: true }),
    r(KEYWORD_WORD_WITH_SPACES_BEFORE_SEP, TT.KW, { pop: true }),
    r(KEYWORD_WORD_BEFORE_SEP, TT.KW, { pop: true }),
    r(KEYWORD_WORD_BEFORE_WS, TT.KW),
    ...base,
];
states.keyword_invocation_no_continue = [
    RULE_NOT_ELLIPSIS_POP,
    ...states.keyword_invocation,
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
    r(/[^\{\}\n:]/, TT.V2),
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
    r(/[^}]/, TT.PR),
];
/** rules for strings with single quotes */
states.single_string = [r(/\\'/, TT.ST), r(/'/, TT.ST, { pop: true }), r(/./, TT.ST)];
/** rules for strings with double quotes */
states.double_string = [r(/\\"/, TT.ST), r(/"/, TT.ST, { pop: true }), r(/./, TT.ST)];
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
    r(/[^\]]/, TT.ST),
];
/** the actual exported function that will install the mode in CodeMirror */
CodeMirror.defineSimpleMode(
    'robotframework',
    __assign({
        meta: {
            dontIndentStates: ['comment'],
            lineComment: '#'
        }
    }, states)
);
CodeMirror.defineMIME(
    'text/x-robotframework',
    'robotframework'
);
CodeMirror.modeInfo.push({
    ext: ['robot', 'resource'],
    mime: 'text/x-robotframework',
    mode: 'robotframework',
    name: 'robotframework'
});

})();
