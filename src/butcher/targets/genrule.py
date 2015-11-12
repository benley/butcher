"""genrule targets"""

import os
import re
import subprocess
import sys
import stat
from butcher import address
from butcher import error
from butcher.targets import base
from twitter.common import log


class GenRuleBuilder(base.BaseBuilder):
    """Build a genrule."""

    # regex to match $(tags with parentheses) in cmd sublanguage
    paren_tag_re = re.compile(r'(?<!\$)\$\((.+?)\)')

    # regex to match $tags_without_parens in cmd sublanguage
    noparen_tag_re = re.compile(r'(?<!\$)\$([^\$.]+?)(?!\w)')

    # Shell to run cmd subprocesses in:
    shell_bin = '/bin/bash'

    def __init__(self, buildroot, target_obj, source_dir):
        base.BaseBuilder.__init__(self, buildroot, target_obj, source_dir)
        self.cmd = self.rule.params['cmd']
        self.path_to_this_rule = os.path.join(self.buildroot,
                                              self.rule.address.repo,
                                              self.rule.address.path)

    def build(self):
        log.debug('[%s]: Running in a shell:\n  %s', self.rule.name, self.cmd)
        cmd = [self.shell_bin, '-c', self.cmd]
        proc = subprocess.Popen(cmd, shell=False, cwd=self.path_to_this_rule,
                                stdout=sys.stdout, stderr=sys.stderr)
        returncode = proc.wait()
        if returncode != 0:
            raise error.TargetBuildFailed(self.rule.name,
                                          'cmd returned %s.' % (returncode))
        elif self.rule.params['executable']:
            # GenRule.__init__ already ensured that there is only one
            # output file if executable=1 is set.
            built_outfile = os.path.join(self.buildroot,
                                         self.rule.output_files[0])
            built_outfile_stat = os.stat(built_outfile)
            os.chmod(built_outfile, built_outfile_stat.st_mode | stat.S_IEXEC)

    def _metahash(self):
        """Include genrule cmd in the metahash."""
        if self._cached_metahash:
            return self._cached_metahash
        mhash = base.BaseBuilder._metahash(self)
        log.debug('[%s]: Metahash input: cmd="%s"', self.address, self.cmd)
        mhash.update(self.cmd)
        self._cached_metahash = mhash
        return mhash

    def prep(self):
        base.BaseBuilder.prep(self)
        self.expand_cmd_labels()

    def expand_cmd_labels(self):
        """Expand make-style variables in cmd parameters.

        Currently:
        $(location <foo>)     Location of one dependency or output file.
        $(locations <foo>)    Space-delimited list of foo's output files.
        $(SRCS)               Space-delimited list of this rule's source files.
        $(OUTS)               Space-delimited list of this rule's output files.
        $(@D)                 Full path to the output directory for this rule.
        $@                    Path to the output (single) file for this rule.
        """
        cmd = self.cmd

        def _expand_onesrc():
            """Expand $@ or $(@) to one output file."""
            outs = self.rule.params['outs'] or []
            if len(outs) != 1:
                raise error.TargetBuildFailed(
                    self.address,
                    '$@ substitution requires exactly one output file, but '
                    'this rule has %s of them: %s' % (len(outs), outs))
            else:
                return os.path.join(self.buildroot, self.path_to_this_rule,
                                    outs[0])

        # TODO: this function is dumb and way too long
        def _expand_makevar(re_match):
            """Expands one substitution symbol."""
            # Expand $(location foo) and $(locations foo):
            label = None
            tagstr = re_match.groups()[0]
            tag_location = re.match(
                r'\s*location\s+([A-Za-z0-9/\-_:\.]+)\s*', tagstr)
            tag_locations = re.match(
                r'\s*locations\s+([A-Za-z0-9/\-_:\.]+)\s*', tagstr)
            if tag_location:
                label = tag_location.groups()[0]
            elif tag_locations:
                label = tag_locations.groups()[0]
            if label:
                # Is it a filename found in the outputs of this rule?
                if label in self.rule.params['outs']:
                    return os.path.join(self.buildroot, self.address.repo,
                                        self.address.path, label)
                # Is it an address found in the deps of this rule?
                addr = self.rule.makeaddress(label)
                if addr not in self.rule.composed_deps():
                    raise error.TargetBuildFailed(
                        self.address,
                        '%s is referenced in cmd but is neither an output '
                        'file from this rule nor a dependency of this rule.' %
                        label)
                else:
                    paths = [x for x in self.rulefor(addr).output_files]
                    if len(paths) is 0:
                        raise error.TargetBuildFailed(
                            self.address,
                            'cmd refers to %s, but it has no output files.')
                    elif len(paths) > 1 and tag_location:
                        raise error.TargetBuildFailed(
                            self.address,
                            'Bad substitution in cmd: Expected exactly one '
                            'file, but %s expands to %s files.' % (
                                addr, len(paths)))
                    else:
                        return ' '.join(
                            [os.path.join(self.buildroot, x) for x in paths])

            # Expand $(OUTS):
            elif re.match(r'OUTS', tagstr):
                return ' '.join(
                    [os.path.join(self.buildroot, x)
                     for x in self.rule.output_files])

            # Expand $(SRCS):
            elif re.match(r'SRCS', tagstr):
                return ' '.join(os.path.join(self.path_to_this_rule, x)
                                for x in self.rule.params['srcs'] or [])

            # Expand $(@D):
            elif re.match(r'\s*@D\s*', tagstr):
                ruledir = os.path.join(self.buildroot, self.path_to_this_rule)
                return ruledir

            # Expand $(@), $@:
            elif re.match(r'\s*@\s*', tagstr):
                return _expand_onesrc()

            else:
                raise error.TargetBuildFailed(
                    self.address,
                    '[%s] Unrecognized substitution in cmd: %s' % (
                        self.address, re_match.group()))

        cmd, _ = re.subn(self.paren_tag_re, _expand_makevar, cmd)

        # Match tags starting with $ without parens. Will also catch parens, so
        # this goes after the tag_re substitutions.
        cmd, _ = re.subn(self.noparen_tag_re, _expand_makevar, cmd)

        # Now that we're done looking for $(blabla) and $bla parameters, clean
        # up any $$ escaping:
        cmd, _ = re.subn(r'\$\$', '$', cmd)

        # Maybe try heuristic label expansion?  Actually on second thought
        # that's a terrible idea. Use the explicit syntax, you lazy slobs. ;-)

        # TODO: Maybe consider other expansions from the gnu make manual?
        # $^ might be useful.
        # http://www.gnu.org/software/make/manual/html_node/Automatic-Variables.html#Automatic-Variables
        self.cmd = cmd


class GenRule(base.BaseTarget):
    """genrule target

    Arguments:
      name: A unique name for this rule. (required)
      srcs: List of inputs for this rule. (List of labels; optional)
      outs: List of output files generated by this command.
            (List of filenames; required)
      deps: List of dependencies for this rule. Will eventually be deprecated
            in favor of srcs and tools. (List of labels; optional)
      executable: If true, declares the output of this rule to be executable.
                  (Boolean; optional; default is False)
                  Setting this to True means the output is an executable file
                  and can be run using the "butcher run" command. The genrule
                  must produce exactly one output in this case.
      cmd: The command to run. (String; required)
           This argument is subject to some limited Make-style variable
           substitution:
           1. All occurrences of $(location <label>) are replaced by the full
              path to the file denoted by <label>. If <label> is malformed, or
              not a declared dependency of this rule, or does not expand to
              exactly one file, the rule will fail. The label does not need to
              be a canonical address: "foo", ":foo",
              "//fulladdr/to/module:rulename" are all valid.  The label may
              also be the name of an output file from this rule's "outs"
              attribute, in which case only the unqualified form (no // or :)
              may be used.
           2. All occurrences of $(locations <label>) are replaced by a
              space-separated list of paths to the files denoted by <label>.
              Similar to (1), the label must be a well-formed declared
              dependency of this rule, or one of its output files.
           3. $(OUTS) is replaced with a space-delimited list of full paths to
              this rule's output files. If the rule only has one output file,
              you may use $@ to refer to it.
           4. $(@D) is expanded to this rule's output directory.

    Notes:
      * $$ evaluates to $ (a literal dollar sign). For example, "$$$$.tmp" is a
        temporary filename containing the process ID of the shell ($$).
        Similarly, to invoke a shell command containing dollar-signs such as
        "ls $(dirname $x)", you should instead write "$((dirname $x)".
      * cmd should always use $(SRCS) or $(location <srclabel>) to refer to
        sources rather than hard-coding filenames. Likewise, it should use
        $(OUTS), $@, or $(location <outlabel>) to refer to output files. This
        is the only way to ensure that it reads and writes files in the right
        places. (outs does not write into the current directory, and neither
        should you: it may be read-only.)
      * The output directory is created automatically before the cmd runs.
      * In order to produce consistend and repeatible build results, you should
        avoid running binaries or depending on files that are not also built by
        butcher, or at the very least are checked into revision control and
        specified as srcs or deps of this rule. To run a binary built by
        butcher, it is best to refer to it by label, as its filename or
        location on disk may change.

    Examples:

      # The following rule generates a tarball from its srcs using gnu tar,
      # which is built from a hypothetical //tools:gnutar rule elsewhere:
      genrule(
          name = "docs",
          srcs = glob('docs/*.html') + glob('docs/*.png'),
          deps = ["//tools:gnutar"],
          outs = ["myfancydocumentation.tgz"],
          cmd = "$(location //tools:gnutar) czf $@ $(SRCS)",
          )
    """

    # TODO: srcs should really work with both filenames in source tree and
    #       labels referring to other rules. It's going to take some
    #       considerable refactoring of how "addresses" are handled in butcher
    #       to enable that, but I'm pretty sure that is the right way to go.
    # TODO: provide a way to declare user-defined "make" variables(?)
    # TODO: provide usage examples

    rulebuilder = GenRuleBuilder
    ruletype = 'genrule'

    required_params = [('name', str), ('cmd', str), ('outs', list)]
    optional_params = [('srcs', list, None),
                       ('deps', list, None),
                       ('executable', (int, bool), False)]

    def __init__(self, **kwargs):
        base.BaseTarget.__init__(self, **kwargs)

        if len(self.params['outs']) > 1 and self.params['executable']:
            raise error.InvalidRule(
                'executable=1 is only allowed when there is one output file.')

    @property
    def output_files(self):
        """Returns list of output files from this rule, relative to buildroot.

        In this case it's simple (for now) - the output files are enumerated in
        the rule definition.
        """
        outs = [os.path.join(self.address.repo, self.address.path, x)
                for x in self.params['outs']]
        return outs
