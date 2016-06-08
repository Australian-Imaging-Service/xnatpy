from abc import ABCMeta, abstractmethod
from xml.etree import ElementTree

xdat_ns = "http://nrg.wustl.edu/security"
ElementTree.register_namespace("xdat", xdat_ns)


class ORMMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        for key, value in dct.items():
            if isinstance(value, ORMproperty):
                dct[key]._prop_class = cls
                dct[key]._prop_name = key
        super(ORMMeta, cls).__init__(name, bases, dct)


class ORMproperty(property):
    _prop_name = 'unknown'
    _prop_class = None

    def __init__(self, fget, fset=None, fdel=None, doc=None):
        super(ORMproperty, self).__init__(fget=fget, fset=fset, fdel=fdel, doc=doc)

    @property
    def identifier(self):
        return '{}/{}'.format(self._prop_class._XSI_TYPE, self._prop_name)

    def __eq__(self, other):
        return Constraint(self.identifier, '=', other)

    def __gt__(self, other):
        return Constraint(self.identifier, '>', other)

    def __ge__(self, other):
        return Constraint(self.identifier, '>=', other)

    def __lt__(self, other):
        return Constraint(self.identifier, '<', other)

    def __le__(self, other):
        return Constraint(self.identifier, '<=', other)

    def like(self, other):
        return Constraint(self.identifier, ' LIKE ', other)


def and_(*args):
    return CompoundConstraint(tuple(args), 'AND')


def or_(*args):
    return CompoundConstraint(tuple(args), 'OR')


class Query(object):
    def __init__(self, xsi_type, xnat, constraints=None):
        self.xsi_type = xsi_type
        self.xnat = xnat
        self.constraints = constraints

    def filter(self, *constraints):
        if len(constraints) == 0:
            return self
        elif len(constraints) == 1:
            constraints = constraints[0]
        else:
            constraints = CompoundConstraint(constraints, 'AND')

        if self.constraints is not None:
            constraints = CompoundConstraint((self.constraints, constraints), 'AND')

        return Query(self.xsi_type, self.xnat, constraints)

    def to_xml(self):
        # Create main elements
        bundle = ElementTree.Element(ElementTree.QName(xdat_ns, "bundle"))
        root_elem_name = ElementTree.SubElement(bundle, ElementTree.QName(xdat_ns, "root_element_name"))
        root_elem_name.text = self.xsi_type

        # Add search fields
        search_where = ElementTree.SubElement(bundle, ElementTree.QName(xdat_ns, "search_field"))
        element_name = ElementTree.SubElement(search_where, ElementTree.QName(xdat_ns, "element_name"))
        element_name.text = self.xsi_type
        field_id = ElementTree.SubElement(search_where, ElementTree.QName(xdat_ns, "field_ID"))
        field_id.text = 'URL'
        sequence = ElementTree.SubElement(search_where, ElementTree.QName(xdat_ns, "sequence"))
        sequence.text = '0'
        type_ = ElementTree.SubElement(search_where, ElementTree.QName(xdat_ns, "type"))
        type_.text = 'string'
        header = ElementTree.SubElement(search_where, ElementTree.QName(xdat_ns, "header"))
        header.text = 'url'

        # Add criterea
        search_where = ElementTree.SubElement(bundle, ElementTree.QName(xdat_ns, "search_where"))
        search_where.set("method", "AND")
        if self.constraints is not None:
            search_where.append(self.constraints.to_xml())

        return bundle

    def to_string(self):
        return ElementTree.tostring(self.to_xml())

    def all(self):
        result = self.xnat.post('/data/search', format='csv', data=self.to_string())
        return result


class BaseConstraint(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def to_xml(self):
        pass

    def to_string(self):
        return ElementTree.tostring(self.to_xml())

    def __or__(self, other):
        return CompoundConstraint((self, other), 'OR')

    def __and__(self, other):
        return CompoundConstraint((self, other), 'AND')


class CompoundConstraint(BaseConstraint):
    def __init__(self, constraints, operator):
        self.constraints = constraints
        self.operator = operator

    def to_xml(self):
        elem = ElementTree.Element(ElementTree.QName(xdat_ns, "child_set"))
        elem.set("method", self.operator)
        elem.extend(x.to_xml() for x in self.constraints)

        return elem


class Constraint(BaseConstraint):
    def __init__(self, indentifier, operator, right_hand):
        self.indentifier = indentifier
        self.operator = operator
        self.right_hand = right_hand

    def __repr__(self):
        return '<Constrain {} {}({})>'.format(self.indentifier,
                                              self.operator,
                                              self.right_hand)

    def to_xml(self):
        elem = ElementTree.Element(ElementTree.QName(xdat_ns, "criteria"))
        schema_loc = ElementTree.SubElement(elem, ElementTree.QName(xdat_ns, "schema_field"))
        operator = ElementTree.SubElement(elem, ElementTree.QName(xdat_ns, "comparison_type"))
        value = ElementTree.SubElement(elem, ElementTree.QName(xdat_ns, "value"))

        elem.set("override_value_formatting", "0")
        schema_loc.text = self.indentifier
        operator.text = self.operator
        value.text = str(self.right_hand)

        return elem


