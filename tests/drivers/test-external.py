import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node
import pyxb.namespace
import sys
import imp

import os.path

te_generator = pyxb.binding.generate.Generator(allow_absent_module=True, generate_to_files=False)
te_generator.setSchemaRoot(os.path.realpath('%s/../schemas' % (os.path.dirname(__file__),)))
te_generator.addSchemaLocation('test-external.xsd')

# Create a module into which we'll stick the shared types bindings.
# Put it into the sys modules so the import directive in subsequent
# code is resolved.
st = imp.new_module('st')
sys.modules['st'] = st

# Now get the code for the shared types bindings, and evaluate it
# within the new module.

st_generator = pyxb.binding.generate.Generator(allow_absent_module=True, generate_to_files=False)
st_generator.setSchemaRoot(os.path.realpath('%s/../schemas' % (os.path.dirname(__file__),)))
st_generator.addSchemaLocation('shared-types.xsd')

st_modules = st_generator.bindingModules()
assert 1 == len(st_modules)
code = st_modules.pop().moduleContents()
file('st.py', 'w').write(code)
rv = compile(code, 'shared-types', 'exec')
exec code in st.__dict__

# Set the path by which we expect to reference the module
stns = pyxb.namespace.NamespaceForURI('URN:shared-types', create_if_missing=True)
module_record = stns.lookupModuleRecordByUID(st_generator.generationUID())
assert module_record is not None, 'Unable to find %s in ns %s' % (st_generator.generationUID(), stns)
module_record.setModulePath('st')

# Now get and build a module that refers to that module.

modules = te_generator.bindingModules()
assert 1 == len(modules)
m = modules.pop()
assert m.namespace() != stns
code = m.moduleContents()
file('te.py', 'w').write(code)
rv = compile(code, 'test-external', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance):
    return instance.toDOM().documentElement

import unittest

class TestExternal (unittest.TestCase):

    def testSharedTypes (self):
        self.assertEqual(word.typeDefinition()._ElementMap['from'].elementBinding().typeDefinition(), st.english)
        self.assertEqual(word.typeDefinition()._ElementMap['to'].elementBinding().typeDefinition(), st.welsh)
        one = st.english('one')
        self.assertRaises(BadTypeValueError, st.english, 'five')
        # Element constructor without content is error
        self.assertRaises(BadTypeValueError, english)
        self.assertEqual('one', english('one'))
        # Element constructor with out-of-range content is error
        self.assertRaises(BadTypeValueError, english, 'five')

        xml = '<ns1:english xmlns:ns1="URN:test-external">one</ns1:english>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = english.createFromDOM(dom.documentElement)
        self.assertEqual('one', instance)
        self.assertEqual(xml, ToDOM(instance).toxml())

    def testWords (self):
        xml = '<ns1:word xmlns:ns1="URN:test-external"><from>one</from><to>un</to></ns1:word>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = word.createFromDOM(dom.documentElement)
        self.assertEquals('one', instance.from_)
        self.assertEquals('un', instance.to)
        self.assertEqual(xml, ToDOM(instance).toxml())
        
    def testBadWords (self):
        xml = '<ns1:word xmlns:ns1="URN:test-external"><from>five</from><to>pump</to></ns1:word>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(BadTypeValueError, word.createFromDOM, dom.documentElement)

    def testComplexShared (self):
        xml = '<ns1:lwords language="english" newlanguage="welsh" xmlns:ns1="URN:test-external">un</ns1:lwords>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = lwords.createFromDOM(dom.documentElement)
        self.assertEquals(instance._element(), lwords)
        self.assertTrue(isinstance(instance.value(), st.welsh))
        self.assertEquals('english', instance.language)
        self.assertEquals('welsh', instance.newlanguage)

    def testCrossedRestriction (self):
        # Content model elements that are consistent with parent
        # should share its fields; those that change something should
        # override it.
        self.assertEqual(st.extendedName._ElementMap['title'], restExtName._ElementMap['title'])
        self.assertEqual(st.extendedName._ElementMap['forename'], restExtName._ElementMap['forename'])
        self.assertEqual(st.extendedName._ElementMap['surname'], restExtName._ElementMap['surname'])
        self.assertEqual(st.extendedName._ElementMap['generation'], restExtName._ElementMap['generation'])

        xml = '<personName><surname>Smith</surname></personName>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = st.personName.Factory(_dom_node=dom.documentElement)
        xml = '<personName><surname>Smith</surname><generation>Jr.</generation></personName>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, st.personName.Factory, _dom_node=dom.documentElement)
        xml = xml.replace('personName', 'extendedName')
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = st.extendedName.Factory(_dom_node=dom.documentElement)
        xml = xml.replace('extendedName', 'restExtName')
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = restExtName.Factory(_dom_node=dom.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
