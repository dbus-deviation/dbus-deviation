#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright © 2015 Collabora Ltd.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
TODO
"""

import sys
from dbusapi import ast


# Warning categories.
WARNING_CATEGORIES = [
    'info',
    'backwards-compatibility',
    'forwards-compatibility',
]


class InterfaceComparator(object):
    """
    Compare two D-Bus interface descriptions and determine how they differ.

    Differences are given different severity levels, depending on whether they
    affect
     - nothing, and are purely decorative; for example, changing the name of a
       method argument
     - forwards compatibility, where code written against the new interface
       may not work against the old interface; for example, because it uses a
       newly added method
     - backwards compatibility, where code written against the old interface
       may not work against the new interface; for example, because it changes
       the type of a property
    """

    # Output severity levels.
    OUTPUT_INFO = 0
    OUTPUT_FORWARDS_INCOMPATIBLE = 1
    OUTPUT_BACKWARDS_INCOMPATIBLE = 2

    def __init__(self, old_interfaces, new_interfaces,
                 enabled_warnings=WARNING_CATEGORIES):
        self._old_interfaces = old_interfaces
        self._new_interfaces = new_interfaces
        self._output = []
        self._enabled_warnings = enabled_warnings

    def _issue_output(self, level, message):
        self._output.append((level, message))

    def _format_level(self, level):
        return [' INFO', ' WARN', 'ERROR'][level]

    def _get_fd_for_level(self, level):
        if level == self.OUTPUT_INFO:
            return sys.stdout
        return sys.stderr

    def _warning_enabled(self, level):
        return (level == self.OUTPUT_INFO and
                'info' in self._enabled_warnings) or \
               (level == self.OUTPUT_FORWARDS_INCOMPATIBLE and
                'forwards-compatibility' in self._enabled_warnings) or \
               (level == self.OUTPUT_BACKWARDS_INCOMPATIBLE and
                'backwards-compatibility' in self._enabled_warnings)

    def print_output(self):
        """
        Print all the info, warning and error messages generated by the most
        recent call to compare().
        """
        for (level, message) in self._output:
            if not self._warning_enabled(level):
                continue

            formatted_level = self._format_level(level)
            fd = self._get_fd_for_level(level)
            fd.write('%s: %s\n' % (formatted_level, message))

    def get_output(self):
        """
        Return all the info, warning and error messages generated by the most
        recent call to compare().
        """
        out = []

        for (level, message) in self._output:
            if not self._warning_enabled(level):
                continue

            out.append((level, message))

        return out

    def compare(self):
        """
        Compare the two interfaces and store the results. Return the list of
        relevant warnings to output; an empty list otherwise. The
        return value is affected by the categories of enabled warnings.
        """
        self._output = []

        for (name, interface) in self._old_interfaces.items():
            # See if the old interface exists in the new file.
            if name not in self._new_interfaces:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Interface ‘%s’ has been removed.' % name)
            else:
                # Compare the two.
                self._compare_interfaces(interface, self._new_interfaces[name])

        for (name, interface) in self._new_interfaces.items():
            # See if the new interface exists in the old file.
            if name not in self._old_interfaces:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'Interface ‘%s’ has been added.' % name)

        # Work out the exit status.
        return self.get_output()

    def _get_string_annotation(self, node, annotation_name, default):
        if annotation_name in node.annotations:
            return node.annotations[annotation_name].value
        return default

    def _get_bool_annotation(self, node, annotation_name, default):
        if annotation_name in node.annotations:
            return node.annotations[annotation_name].value == 'true'
        return default

    def _get_emits_changed_signal_annotation(self, node):
        # Reference:
        # http://dbus.freedesktop.org/doc/dbus-specification.html\
        # #introspection-format
        annotation_name = 'org.freedesktop.DBus.Property.EmitsChangedSignal'

        if annotation_name in node.annotations:
            return node.annotations[annotation_name].value
        elif isinstance(node, ast.ASTProperty):
            assert node.interface is not None
            return self._get_emits_changed_signal_annotation(node.interface)
        else:
            return 'true'

    def _compare_annotations(self, old_node, new_node):
        # Reference:
        # http://dbus.freedesktop.org/doc/dbus-specification.html\
        # #introspection-format
        old_deprecated = \
            self._get_bool_annotation(old_node,
                                      'org.freedesktop.DBus.Deprecated', False)
        new_deprecated = \
            self._get_bool_annotation(new_node,
                                      'org.freedesktop.DBus.Deprecated', False)

        if old_deprecated and not new_deprecated:
            self._issue_output(self.OUTPUT_INFO,
                               'Node ‘%s’ has been un-deprecated.' %
                               old_node.format_name())
        elif not old_deprecated and new_deprecated:
            self._issue_output(self.OUTPUT_INFO,
                               'Node ‘%s’ has been deprecated.' %
                               old_node.format_name())

        old_c_symbol = \
            self._get_string_annotation(old_node,
                                        'org.freedesktop.DBus.GLib.CSymbol',
                                        '')
        new_c_symbol = \
            self._get_string_annotation(new_node,
                                        'org.freedesktop.DBus.GLib.CSymbol',
                                        '')

        if old_c_symbol != new_c_symbol:
            self._issue_output(self.OUTPUT_INFO,
                               'Node ‘%s’ has changed its C symbol from ‘%s’ '
                               'to ‘%s’.' %
                               (old_node.format_name(), old_c_symbol,
                                new_c_symbol))

        old_no_reply = \
            self._get_bool_annotation(old_node,
                                      'org.freedesktop.DBus.Method.NoReply',
                                      False)
        new_no_reply = \
            self._get_bool_annotation(new_node,
                                      'org.freedesktop.DBus.Method.NoReply',
                                      False)

        if old_no_reply and not new_no_reply:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Node ‘%s’ has been marked as returning a '
                               'reply.' % old_node.format_name())
        elif not old_no_reply and new_no_reply:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Node ‘%s’ has been marked as not returning a '
                               'reply.' % old_node.format_name())

        old_ecs = self._get_emits_changed_signal_annotation(old_node)
        new_ecs = self._get_emits_changed_signal_annotation(new_node)

        if (old_ecs in ['true', 'invalidates'] and
            new_ecs in ['false', 'const']):
            self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                               'Node ‘%s’ stopped emitting '
                               'org.freedesktop.DBus.PropertiesChanged.' %
                               old_node.format_name())
        elif (old_ecs in ['false', 'const'] and
              new_ecs in ['true', 'invalidates']):
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Node ‘%s’ started emitting '
                               'org.freedesktop.DBus.PropertiesChanged.' %
                               old_node.format_name())
        elif old_ecs == 'true' and new_ecs == 'invalidates':
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Node ‘%s’ stopped emitting its new value in '
                               'org.freedesktop.DBus.PropertiesChanged.' %
                               old_node.format_name())
        elif old_ecs == 'invalidates' and new_ecs == 'true':
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Node ‘%s’ started emitting its new value in '
                               'org.freedesktop.DBus.PropertiesChanged.' %
                               old_node.format_name())
        elif old_ecs == 'const' and new_ecs == 'false':
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Node ‘%s’ stopped being a constant.' %
                               old_node.format_name())
        elif old_ecs == 'false' and new_ecs == 'const':
            self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                               'Node ‘%s’ became a constant.' %
                               old_node.format_name())

    def _compare_interfaces(self, old_interface, new_interface):
        # Precondition of calling this method.
        assert old_interface.name == new_interface.name

        # Compare methods.
        for (name, method) in old_interface.methods.items():
            if name not in new_interface.methods:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Method ‘%s’ has been removed.' %
                                   method.format_name())
            else:
                self._compare_methods(method, new_interface.methods[name])

        for (name, method) in new_interface.methods.items():
            if name not in old_interface.methods:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'Method ‘%s’ has been added.' %
                                   method.format_name())

        # Compare properties
        for (name, property) in old_interface.properties.items():
            if name not in new_interface.properties:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Property ‘%s’ has been removed.' %
                                   property.format_name())
            else:
                self._compare_properties(property,
                                         new_interface.properties[name])

        for (name, property) in new_interface.properties.items():
            if name not in old_interface.properties:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'Property ‘%s’ has been added.' %
                                   property.format_name())

        # Compare signals
        for (name, signal) in old_interface.signals.items():
            if name not in new_interface.signals:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Signal ‘%s’ has been removed.' %
                                   signal.format_name())
            else:
                self._compare_signals(signal,
                                      new_interface.signals[name])

        for (name, signal) in new_interface.signals.items():
            if name not in old_interface.signals:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'Signal ‘%s’ has been added.' %
                                   signal.format_name())

        # Compare annotations
        self._compare_annotations(old_interface, new_interface)

    def _compare_methods(self, old_method, new_method):
        # Precondition of calling this method.
        assert old_method.name == new_method.name

        # Compare the argument lists.
        n_old_args = len(old_method.arguments)
        n_new_args = len(new_method.arguments)

        for i in range(max(n_old_args, n_new_args)):
            if i >= n_old_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Argument %s of method ‘%s’ '
                                   'has been added.' %
                                   (new_method.arguments[i].format_name(),
                                    new_method.format_name()))
            elif i >= n_new_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Argument %s of method ‘%s’ '
                                   'has been removed.' %
                                   (old_method.arguments[i].format_name(),
                                    old_method.format_name()))
            else:
                self._compare_arguments(old_method.arguments[i],
                                        new_method.arguments[i])

        # Compare annotations
        self._compare_annotations(old_method, new_method)

    def _compare_properties(self, old_property, new_property):
        # Precondition of calling this method.
        assert old_property.name == new_property.name

        if old_property.type != new_property.type:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Property ‘%s’ has changed type from ‘%s’ '
                               'to ‘%s’.' %
                               (old_property.format_name(),
                                old_property.type, new_property.type))

        if (old_property.access == ast.ASTProperty.ACCESS_READ or
            old_property.access == ast.ASTProperty.ACCESS_WRITE) and \
           new_property.access == ast.ASTProperty.ACCESS_READWRITE:
            # Property has become less restrictive.
            self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                               'Property ‘%s’ has changed access from '
                               '‘%s’ to ‘%s’, becoming less restrictive.' %
                               (old_property.format_name(),
                                old_property.access, new_property.access))
        elif old_property.access != new_property.access:
            # Access has changed incompatibly.
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Property ‘%s’ has changed access from '
                               '‘%s’ to ‘%s’.' %
                               (old_property.format_name(),
                                old_property.access, new_property.access))

        # Compare annotations
        self._compare_annotations(old_property, new_property)

    def _compare_signals(self, old_signal, new_signal):
        # Precondition of calling this method.
        assert old_signal.name == new_signal.name

        # Compare the argument lists.
        n_old_args = len(old_signal.arguments)
        n_new_args = len(new_signal.arguments)

        for i in range(max(n_old_args, n_new_args)):
            if i >= n_old_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Argument %s of signal ‘%s’ '
                                   'has been added.' %
                                   (new_signal.arguments[i].format_name(),
                                    new_signal.format_name()))
            elif i >= n_new_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'Argument %s of signal ‘%s’ '
                                   'has been removed.' %
                                   (old_signal.arguments[i].format_name(),
                                    old_signal.format_name()))
            else:
                self._compare_arguments(old_signal.arguments[i],
                                        new_signal.arguments[i])

        # Compare annotations
        self._compare_annotations(old_signal, new_signal)

    def _compare_arguments(self, old_arg, new_arg):
        if old_arg.name != new_arg.name:
            self._issue_output(self.OUTPUT_INFO,
                               'Argument %u of ‘%s’ has changed '
                               'name from ‘%s’ to ‘%s’.' %
                               (old_arg.index, old_arg.parent.format_name(),
                                old_arg.name, new_arg.name))

        if old_arg.type != new_arg.type:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Argument %u of ‘%s’ has changed '
                               'type from ‘%s’ to ‘%s’.' %
                               (old_arg.index, old_arg.parent.format_name(),
                                old_arg.type, new_arg.type))

        if old_arg.direction != new_arg.direction:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'Argument %u of ‘%s’ has changed '
                               'direction from ‘%s’ to ‘%s’.' %
                               (old_arg.index, old_arg.parent.format_name(),
                                old_arg.direction, new_arg.direction))

        # Compare annotations
        self._compare_annotations(old_arg, new_arg)
