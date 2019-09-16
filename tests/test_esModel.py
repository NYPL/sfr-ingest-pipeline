import pytest

from model.elasticModel import Rights, Subject, Agent


class TestRights(object):
    def test_rightsFields(self):
        assert sorted(Rights.getFields()) == sorted([
            'source',
            'license',
            'rights_statement',
            'rights_reason'
        ])
    
    def test_rightsHash(self):
        testRights = Rights(
            source='test',
            license='CC0',
            rights_statement='testing'
        )
        assert hash(testRights) == hash(('test', 'CC0', 'testing'))
    
    def test_rightsEq(self):
        rightsComp = [
            Rights(
                source='test',
                license='CC0',
                rights_statement='testing'
            )
            for i in range(2)
        ]

        assert rightsComp[0] == rightsComp[1]
    
    def test_rightsInequal(self):
        rightsComp = [
            Rights(
                source='test',
                license='CC0',
                rights_statement='testing'
            ),
            'otherThing'
        ]
        assert rightsComp[0] != rightsComp[1]


class TestSubjects(object):
    def test_subjectFields(self):
        assert sorted(Subject.getFields()) == sorted(['uri', 'authority', 'subject'])


class TestAgent(object):
    def test_agentFields(self):
        assert sorted(Agent.getFields()) == sorted([
            'name',
            'sort_name',
            'lcnaf',
            'viaf',
            'biography'
        ])
    
    def test_AgentHash(self):
        testAgent = Agent(
            name='Tester, Test',
            lcnaf='n000000',
            viaf='xxxxxxxxx'
        )
        assert hash(testAgent) == hash(('Tester, Test', 'n000000', 'xxxxxxxxx'))
    
    def test_AgentEq(self):
        agentComp = [
            Agent(
                name='Tester, Test',
                lcnaf='n000000',
                viaf='xxxxxxxxx'
            )
            for i in range(2)
        ]

        assert agentComp[0] == agentComp[1]
