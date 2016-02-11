#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
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
Unit tests for dbusapi.ast.parse
"""


# pylint: disable=missing-docstring


from dbusapi.ast import (parse, DuplicateNodeError,
                         UnknownNodeError, MissingAttributeError, Loggable)
import os
import tempfile
import unittest


def _create_temp_xml_file(xml):
    """Create a temporary XML file with the given contents."""
    tmp_fd, tmp_name = tempfile.mkstemp(suffix='.xml', text=True)
    xml_fd = os.fdopen(tmp_fd, 'wt')
    xml_fd.write(xml)
    xml_fd.close()

    return tmp_name


def _test_parsing(xml, recover=False):
    """Parse the XML snippet"""
    tmpfile = _create_temp_xml_file(xml)
    interfaces = parse(tmpfile, recover)
    os.unlink(tmpfile)

    return (interfaces, tmpfile)


# pylint: disable=too-many-public-methods
class TestParserErrors(unittest.TestCase):
    """Test error handling in when parsing XML."""

    def test_unknown_root_node(self):
        xml = ("<notnode><irrelevant/></notnode>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown root node ‘notnode’.')

    def test_duplicate_interface(self):
        xml = ("<node><interface name='I'/><interface name='I'/></node>")
        with self.assertRaises(DuplicateNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Duplicate interface definition ‘I’.')

    def test_unknown_interface_node(self):
        xml = ("<node><badnode/></node>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown node ‘badnode’ in root.')

    def test_interface_missing_name(self):
        xml = ("<node><interface/></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(
            cm.exception.message,
            'Missing required attribute ‘name’ in interface.')

    def test_duplicate_method(self):
        xml = ("<node><interface name='I'>"
               "<method name='M'/><method name='M'/>"
               "</interface></node>")
        with self.assertRaises(DuplicateNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(
            cm.exception.message,
            'Duplicate method definition ‘I.M’.')

    def test_duplicate_signal(self):
        xml = ("<node><interface name='I'>"
               "<signal name='S'/><signal name='S'/>"
               "</interface></node>")
        with self.assertRaises(DuplicateNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(
            cm.exception.message,
            'Duplicate signal definition ‘I.S’.')

    def test_duplicate_property(self):
        xml = ("<node><interface name='I'>"
               "<property name='P' type='s' access='readwrite'/>"
               "<property name='P' type='s' access='readwrite'/>"
               "</interface></node>")
        with self.assertRaises(DuplicateNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Duplicate property definition ‘I.P’.')

    def test_unknown_sub_interface_node(self):
        xml = ("<node><interface name='I'><badnode/></interface></node>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown node ‘badnode’ in interface ‘I’.')

    def test_method_missing_name(self):
        xml = ("<node><interface name='I'><method/></interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘name’ in method.')

    def test_unknown_method_node(self):
        xml = ("<node><interface name='I'>"
               "<method name='M'><badnode/></method>"
               "</interface></node>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown node ‘badnode’ in method ‘M’.')

    def test_signal_missing_name(self):
        xml = ("<node><interface name='I'><signal/></interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘name’ in signal.')

    def test_unknown_signal_node(self):
        xml = ("<node><interface name='I'>"
               "<signal name='S'><badnode/></signal>"
               "</interface></node>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown node ‘badnode’ in signal ‘S’.')

    def test_property_missing_name(self):
        xml = ("<node><interface name='I'>"
               "<property type='s' access='readwrite'/>"
               "</interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘name’ in property.')

    def test_property_missing_type(self):
        xml = ("<node><interface name='I'>"
               "<property name='P' access='readwrite'/>"
               "</interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘type’ in property.')

    def test_property_missing_access(self):
        xml = ("<node><interface name='I'>"
               "<property name='P' type='s'/>"
               "</interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘access’ in property.')

    def test_unknown_property_node(self):
        xml = ("<node><interface name='I'>"
               "<property name='P' type='s' access='readwrite'>"
               "<badnode/></property>"
               "</interface></node>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown node ‘badnode’ in property ‘P’.')

    def test_unknown_arg_node(self):
        xml = ("<node><interface name='I'>"
               "<method name='M'><arg type='s'><badnode/></arg></method>"
               "</interface></node>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown node ‘badnode’ in argument ‘unnamed’.')

    def test_arg_missing_type(self):
        xml = ("<node><interface name='I'>"
               "<method name='M'><arg/></method>"
               "</interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘type’ in arg.')

    def test_annotation_missing_name(self):
        xml = ("<node><interface name='I'>"
               "<annotation value='V'/>"
               "</interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘name’ in annotation.')

    def test_annotation_missing_value(self):
        xml = ("<node><interface name='I'>"
               "<annotation name='N'/>"
               "</interface></node>")
        with self.assertRaises(MissingAttributeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Missing required attribute ‘value’ in annotation.')

    def test_unknown_annotation_node(self):
        xml = ("<node><interface name='I'>"
               "<annotation name='N' value='V'><badnode/></annotation>"
               "</interface></node>")
        with self.assertRaises(UnknownNodeError) as cm:
            (interfaces, filename) = _test_parsing(xml)
        self.assertEquals(cm.exception.message,
                          'Unknown node ‘badnode’ in annotation ‘N’.')


# pylint: disable=too-many-public-methods
class TestParserNormal(unittest.TestCase):
    """Test normal parsing of unusual input."""

    # pylint: disable=invalid-name
    def assertParse(self, xml):  # noqa
        (interfaces, _) = _test_parsing(xml)
        return interfaces

    def test_tp_spec_root(self):
        
        """Test that specifications wrapped in tp:spec are parsed."""
        self.assertParse(
            "<tp:spec xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "'><node><interface name='I'/></node></tp:spec>")

    def test_doc_root(self):
        """Test that doc tags are ignored in the root."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</node>")

    def test_doc_interface(self):
        """Test that doc tags are ignored in interfaces."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</interface></node>")

    def test_doc_method(self):
        """Test that doc tags are ignored in methods."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I'><method name='M'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</method></interface></node>")

    def test_doc_signal(self):
        """Test that doc tags are ignored in signals."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I'><signal name='S'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</signal></interface></node>")

    def test_doc_property(self):
        """Test that doc tags are ignored in properties."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I'><property name='P' type='s' access='read'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</property></interface></node>")

    def test_doc_arg(self):
        """Test that doc tags are ignored in args."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I'><method name='M'><arg type='s'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</arg></method></interface></node>")

    def test_doc_annotation(self):
        """Test that doc tags are ignored in annotations."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I'><annotation name='A' value='V'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</annotation></interface></node>")

    def test_doc_comments(self):
        """Test that xml comments are *not* ignored"""
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<!--"
               "Please consider me"
               "-->"
               "<interface name='I'>"
               "<!--"
               "Notice me too"
               "-->"
               "<method name='foo'>"
               "<!--"
               "And me!"
               "-->"
               "<arg name='bar' type='s'/>"
               "</method>"
               "</interface></node>")

        (interfaces, _) = _test_parsing(xml)
        interface = interfaces.get('I')
        self.assertIsNotNone(interface)
        self.assertEquals(interface.comment, "Please consider me")
        meth = interface.methods.get('foo')
        self.assertIsNotNone(meth)
        self.assertEquals(meth.comment, "Notice me too")
        self.assertEquals(len(meth.arguments), 1)
        arg = meth.arguments[0]
        self.assertEquals(arg.comment, "And me!")

    def test_doc_annotations(self):
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<interface name='I'>"
               "<annotation name='org.gtk.GDBus.DocString' value='bla'/>"
               "</interface></node>")
        (interfaces, _) = _test_parsing(xml)
        interface = interfaces.get('I')
        self.assertIsNotNone(interface)
        self.assertEquals(interface.comment, "bla")

    def test_multiline_comments(self):
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<!--"
               "    Please consider that\n"
               "    multiline comment"
               "-->"
               "<interface name='I'>"
               "</interface></node>")

        (interfaces, _) = _test_parsing(xml)
        interface = interfaces.get('I')
        self.assertIsNotNone(interface)
        self.assertEquals(interface.comment,
                          "    Please consider that\n"
                          "    multiline comment")

    def test_ignored_comments(self):
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<!--"
               "Please ignore that comment"
               "-->"
               "<tp:copyright>"
               "</tp:copyright>"
               "<interface name='I'>"
               "</interface></node>")

        (interfaces, _) = _test_parsing(xml)
        interface = interfaces.get('I')
        self.assertIsNotNone(interface)
        self.assertIsNone(interface.comment)


class TestParserOutputCodes(unittest.TestCase):
    """Test the output codes from Loggable."""

    def test_unique(self):
        codes = Loggable.get_error_codes()
        self.assertEqual(len(codes), len(set(codes)))

    def test_non_empty(self):
        codes = Loggable.get_error_codes()
        self.assertNotEqual(codes, [])


# pylint: disable=too-many-public-methods
class TestParserRecovery(unittest.TestCase):
    """
    Test recovery from parser errors in Loggable to detect subsequent
    errors.
    """

    # pylint: disable=invalid-name
    def assertOutput(self, xml, partial_output):  # noqa
        Loggable.reset()
        (interfaces, filename) = _test_parsing(xml, recover=True)
        self.assertEqual(interfaces, None)
        actual_output = \
            [(filename, 'parser', i[0], i[1]) for i in partial_output]
        self.assertEqual(Loggable.log, actual_output)
        return interfaces

    def test_annotation_interface(self):
        """Test recovery from invalid annotations in an interface."""
        self.assertOutput(
            "<node><interface name='I'>"
            "<annotation/><method/>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘value’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘name’ in method.'),
            ])

    def test_annotation_method(self):
        """Test recovery from invalid annotations in a method."""
        self.assertOutput(
            "<node><interface name='I'><method name='M'>"
            "<annotation/><arg/>"
            "</method></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘value’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘type’ in arg.'),
            ])

    def test_annotation_signal(self):
        """Test recovery from invalid annotations in a signal."""
        self.assertOutput(
            "<node><interface name='I'><signal name='S'>"
            "<annotation/><arg/>"
            "</signal></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘value’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘type’ in arg.'),
            ])

    def test_annotation_property(self):
        """Test recovery from invalid annotations in a property."""
        self.assertOutput(
            "<node><interface name='I'>"
            "<property name='P' type='s' access='read'>"
            "<annotation/><badnode/>"
            "</property>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘value’ in annotation.'),
                ('unknown-node',
                 'Unknown node ‘badnode’ in property ‘P’.'),
            ])

    def test_annotation_arg(self):
        """Test recovery from invalid annotations in an arg."""
        self.assertOutput(
            "<node><interface name='I'><method name='M'><arg type='s'>"
            "<annotation/><badnode/>"
            "</arg></method></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘value’ in annotation.'),
                ('unknown-node',
                 'Unknown node ‘badnode’ in argument ‘unnamed’.'),
            ])


if __name__ == '__main__':
    # Run test suite
    unittest.main()
