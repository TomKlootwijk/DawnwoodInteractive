"""Source-declared resident construction and retention of computational SDFs.

The authored source documents declare numerical roles and the complete graph.
Resident action constructs instruction/child-reference data in returned state;
no host candidate solver participates in an epoch. This is a bounded grammar.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

try:
    from . import source_cycle as cycle_binding
    from . import source_program as author
    from . import source_graph as graph_compiler
    from . import source_graph_types as nominal
    from . import source_resident_v3 as resident
    from . import source_ir_v2 as ir
    from . import source_development_bindings as bindings
    from . import source_development_fidelity as development_fidelity
    from . import development_sdf as sdf
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from local_lab import source_cycle as cycle_binding, source_program as author
    from local_lab import source_graph as graph_compiler, source_graph_types as nominal
    from local_lab import source_resident_v3 as resident, source_ir_v2 as ir
    from local_lab import source_development_bindings as bindings, development_sdf as sdf
    from local_lab import source_development_fidelity as development_fidelity

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'DWI-SDF-DEVELOPMENT-0.1'
RECORD_KEY = 'resource_definition'
SOURCE_INDEX = 31
PROGRAM_FIELDS = {name: 'sdf_' + name for name in bindings.PROGRAM_NAMES}
DIAGNOSTIC_TYPES = {
    'query_x': 'resource_coordinate', 'query_y': 'resource_coordinate', 'quota': 'resource_coordinate',
    'score': 'objective', 'coverage': 'coefficient', 'witness_x': 'resource_coordinate',
    'witness_y': 'resource_coordinate', 'witness_distance': 'resource_distance',
    'accepted': 'bit', 'improvement': 'objective', 'distance': 'resource_distance',
    'trials': 'program_revision', 'previous_score': 'objective', 'enabled': 'bit', 'admitted': 'bit',
}
DIAGNOSTIC_FIELDS = {name: 'resource_' + name for name in DIAGNOSTIC_TYPES}
DEFAULT_TRAINING = [[.71,.15],[.72,.16],[.73,.17],
                    [.15,.71],[.16,.72],[.17,.73],
                    [.41,.41],[.42,.42],[.43,.43]]
V = cycle_binding.V


def state(name): return {'state': name}
def ref(node, output): return {'node': node, 'output': output}
def literal(value, kind): return {'literal': value, 'type': kind}


def make_model(base_model=None):
    """Supply the explicit additional situated record alongside the source core."""
    model = deepcopy(base_model) if base_model is not None else ir.read_json(cycle_binding.MODEL)[0]
    if len(model['operators']) != 31:
        raise ValueError('make_model requires the original 31-record source model')
    function = lambda inputs, outputs, meaning: {
        'inputs': inputs, 'outputs': outputs, 'requires': [], 'source': PROFILE,
        'meaning': meaning, 'status': 'Explicit source binding; separately verified.'}
    record = {'key': RECORD_KEY, 'index': SOURCE_INDEX,
              'label': 'Developing resource-admissibility SDF',
              'role': 'Construct, evaluate and retain executable exact-distance regions from returned evidence.',
              'body': {'resident_binding': {'kind':'selected_body', 'mutation_policy':'preserve_family',
                   'function': function([*cycle_binding.PAIR, 'routing_phase', 'field_distance'],
                       {name:V(name) for name in cycle_binding.PAIR},
                       'Selected-wave interface preserves the pair; development roles and current program data are declared in the accompanying development source.')}},
              'field': {'resident_binding': {'kind':'field', 'mutation_policy':'preserve_program',
                   'function': function(['dx','dy','radius'],
                       {'distance': cycle_binding.sub(cycle_binding.op('sqrt', cycle_binding.add(cycle_binding.sq(V('dx')),cycle_binding.sq(V('dy')))),V('radius'))},
                       'Euclidean local carrier disk distance; distinct from the resource-coordinate SDF interpreted by body roles.')}},
              'placement': {'resident_binding': {'kind':'placement', 'mutation_policy':'preserve_program',
                   'function': function(['u','v','orientation'], {name:V(name) for name in ('u','v','orientation')},
                       'Explicit identity local placement; quotient lifting belongs to the current situated call chain.')}},
              'parameters': dict(zip(author.catalogue.RECORD_VALUES,
                  [.375,.625,0,.18,1,0,0,.4,0,.001,.002,0,0,34,0,0,0,0,0,0]))}
    model['operators'].append(record)
    return model


def make_spec(training_points=None, *, query=(.16,.72), quota=1., enabled=1,
              base_half_extent=.045, complexity_cost=.02, area_cost=.005):
    points = deepcopy(DEFAULT_TRAINING if training_points is None else training_points)
    policy = dict(base_half_extent=base_half_extent, complexity_cost=complexity_cost, area_cost=area_cost)
    protected = dict(proof_margin=bindings.PROOF_MARGIN, separation_margin=0.,
                     native_admission_margin=2*bindings.PROOF_MARGIN, coverage_margin=bindings.PROOF_MARGIN)
    numerical = bindings.make_bindings(points, **policy, admission_margin=protected['native_admission_margin'])
    return {'profile': PROFILE, 'training_points': points, 'policy': policy, 'protected': protected,
            'bindings': numerical,
            'initial': {'program': sdf.single_box_program([.72,.16,.03,.03]),
                        'quota': quota, 'query': list(query), 'enabled': enabled}}


def validate_spec(spec):
    ir.exact_keys(spec, {'profile','training_points','policy','protected','bindings','initial'},
                  {'profile','training_points','policy','protected','bindings','initial'}, 'development source')
    if spec['profile'] != PROFILE:
        raise ValueError('Unknown development source profile')
    protected = {'proof_margin': bindings.PROOF_MARGIN, 'separation_margin':0.,
                 'native_admission_margin':2*bindings.PROOF_MARGIN,
                 'coverage_margin':bindings.PROOF_MARGIN}
    if spec['protected'] != protected:
        raise ValueError('This development edition requires its declared protected margins')
    ir.exact_keys(spec['policy'], {'base_half_extent','complexity_cost','area_cost'},
                  {'base_half_extent','complexity_cost','area_cost'}, 'development policy')
    expected = bindings.make_bindings(spec['training_points'], **spec['policy'],
                                      admission_margin=protected['native_admission_margin'])
    # Protected functions and construction vocabulary are explicit authored
    # source, whose present edition has a fixed meaning. A changed law requires
    # a new declared edition rather than quietly weakening admission/objective.
    if not resident.same_structure(spec['bindings'], expected):
        raise ValueError('Development numerical declarations differ from this edition; declare and verify a new numerical profile')
    initial = spec['initial']
    ir.exact_keys(initial, {'program','quota','query','enabled'}, {'program','quota','query','enabled'}, 'development.initial')
    quota = ir.fp32(initial['quota'], 'quota')[0]
    if not 8*bindings.PROOF_MARGIN < quota <= 16:
        raise ValueError('Initial quota is outside the admitted numerical domain')
    if type(initial['enabled']) not in (int,float) or initial['enabled'] not in (0,1):
        raise ValueError('Construction enabled flag must be a bit')
    if not isinstance(initial['query'], list) or len(initial['query']) != 2:
        raise ValueError('Initial query must have two coordinates')
    query = [ir.fp32(value, 'query coordinate')[0] for value in initial['query']]
    if any(abs(value)>16 for value in query):
        raise ValueError('Initial query exceeds the bounded evaluation envelope')
    certificate = sdf.validate_program(initial['program'], beta=quota,
                                        proof_margin=protected['native_admission_margin'])
    if not certificate['admissible']:
        raise ValueError('Initial definition fails protected geometry admission')
    program = certificate['packed_program']
    n = program['node_count']
    for i, node in enumerate(program['nodes']):
        want = ([0,0,0] if i>=n else [1,0,0] if i==0 else
                [1,(i+1)//2,0] if i%2 else [2,i-2,i-1])
        if node != want:
            raise ValueError('This resident constructor requires canonical left-associated postorder code')
    return program, quota, query


class DevelopmentGraph:
    def __init__(self, definition, graph, spec, metadata):
        self.d, self.g, self.spec, self.meta = definition, graph, spec, metadata
        self.roles = metadata['roles']
        self.nodes = graph['phases'][0]['nodes']

    def helper(self, name, entry):
        self.g['functions'][name] = deepcopy(entry)
        self.g['functions'][name].pop('meaning',None)

    def call(self, node_id, binding_name, args, *, nodes=None, mutation=False):
        node = {'id':node_id,'op':'call_record','record':{'key':'mutation' if mutation else RECORD_KEY},
                'bank':'old' if mutation else 'published','slot':'body',
                'role':2 if mutation else self.roles[binding_name], 'args':args}
        (self.nodes if nodes is None else nodes).append(node)
        return {name:ref(node_id,name) for name in self.spec['bindings'][binding_name]['outputs']}

    def pure(self, node_id, function, args, outputs, *, nodes=None):
        (self.nodes if nodes is None else nodes).append({'id':node_id,'op':'call_helper','function':function,'args':args})
        return {name:ref(node_id,name) for name in outputs}

    def validate(self, label, program):
        code = self.call(label+'_code', 'validate_code', {k:program[k] for k in bindings.HEADER_NAMES+bindings.CODE_NAMES})
        args = {k:program[k] for k in bindings.BOX_NAMES}
        args['node_count'] = program['node_count']
        boxes = self.call(label+'_boxes','validate_geometry_boxes', {**args,'quota':state(DIAGNOSTIC_FIELDS['quota'])})
        separation = self.call(label+'_separation','validate_geometry_separation',args)
        geometry = self.call(label+'_geometry','validate_geometry',{**boxes,**separation})
        return code['valid'],geometry['valid']

    def select_program(self, label, condition, new, old):
        result = {}
        for group, names in [('code',bindings.HEADER_NAMES+bindings.CODE_NAMES),('boxes',bindings.BOX_NAMES)]:
            fn = 'development_select_'+group
            args = {'condition':condition, **{'new_'+k:new[k] for k in names}, **{'old_'+k:old[k] for k in names}}
            result.update(self.pure(label+'_'+group,fn,args,names))
        return result

    def distance(self, label, program, x, y):
        leaf = self.call(label+'_leaf','leaf_distances', {'x':x,'y':y,**{k:program[k] for k in bindings.BOX_NAMES}})
        values = {}
        for binding_name in ('interpret_prefix','interpret_middle','interpret'):
            args = {k:program[k] if k in program else leaf[k] if k in leaf else values[k]
                    for k in self.spec['bindings'][binding_name]['inputs']}
            current = self.call(label+'_'+binding_name,binding_name,args)
            values.update(current)
        return values['distance']

    def score(self,label,program):
        distances = {}
        for i,(x,y) in enumerate(self.spec['training_points']):
            distances['d'+str(i)] = self.distance(label+'_sample'+str(i),program,
                literal(x,'resource_coordinate'),literal(y,'resource_coordinate'))
        score = self.call(label+'_score','score', {**distances,'node_count':program['node_count'],
                          **{k:program[k] for k in bindings.BOX_NAMES}})
        return score

    def install_helpers(self):
        c = cycle_binding
        for group,names in [('code',bindings.HEADER_NAMES+bindings.CODE_NAMES),('boxes',bindings.BOX_NAMES)]:
            inputs = {'condition':'bit', **{'new_'+k:bindings.PROGRAM_TYPES[k] for k in names},
                      **{'old_'+k:bindings.PROGRAM_TYPES[k] for k in names}}
            outputs = {k:bindings.PROGRAM_TYPES[k] for k in names}
            self.helper('development_select_'+group, bindings._entry(inputs,outputs,
                {k:c.choose(V('condition'),V('new_'+k),V('old_'+k)) for k in names},
                'Select each corresponding program word under one guarded condition.',[c.bit_guard(V('condition'))]))
        self.helper('development_require_live',bindings._entry(
            {'code':'bit','geometry':'bit','query_x':'resource_coordinate','query_y':'resource_coordinate','enabled':'bit'},
            {'valid':'bit'}, {'valid':1}, 'Malformed live definitions fail before interpretation.',
            [c.eq(V('code'),1),c.eq(V('geometry'),1),c.le(c.abs_(V('query_x')),16),c.le(c.abs_(V('query_y')),16),c.bit_guard(V('enabled'))]))
        self.helper('development_candidate_valid',bindings._entry(
            {'code':'bit','geometry':'bit','proposed':'bit'}, {'valid':'bit'},
            {'valid':bindings.both(V('code'),V('geometry'),V('proposed'))},
            'All candidate gates must pass before candidate data can be interpreted.',
            [c.bit_guard(V(k)) for k in ('code','geometry','proposed')]))
        self.helper('development_descriptor_encode',bindings._entry(
            {'source_index':'index','x':'resource_coordinate','y':'resource_coordinate','half':'resource_coordinate',
             'valid':'bit','enabled':'bit','revision':'program_revision',
             **{f'old_{i}':'reserved_scalar' for i in range(5)}},
            {f'reserved_{i}':'reserved_scalar' for i in range(5)},
            {f'reserved_{i}':c.choose(c.eq(V('source_index'),SOURCE_INDEX),
                V(('x','y','half')[i]) if i<3 else
                bindings.both(V('valid'),V('enabled'),c.lt(V('revision'),sdf.MAX_REVISION)) if i==3 else 0,
                V(f'old_{i}')) for i in range(5)},
            'Only the resource record receives the old-mutator edit descriptor; all other reserved words retain old values.',
            [c.bit_guard(V('valid')),c.bit_guard(V('enabled'))]))
        self.helper('development_descriptor_decode',bindings._entry(
            {f'reserved_{i}':'reserved_scalar' for i in range(5)},
            {'x':'resource_coordinate','y':'resource_coordinate','half':'resource_coordinate','valid':'bit'},
            {name:V(f'reserved_{i}') for i,name in enumerate(('x','y','half','valid'))},
            'Decode the published descriptor with a guarded eligibility bit.',
            [c.bit_guard(V('reserved_3')),c.eq(V('reserved_4'),0)]))
        self.helper('development_diagnostics',bindings._entry(
            {'distance':'resource_distance','trials':'program_revision'},
            {'admitted':'bit','trials':'program_revision'},
            {'admitted':c.le(V('distance'),0),'trials':c.add(V('trials'),1)},
            'Return accepted-program query admission and a bounded attempted-epoch count.',
            [c.eq(V('trials'),c.op('floor',V('trials'))),c.le(0,V('trials')),c.lt(V('trials'),sdf.MAX_REVISION)]))
        score_types = self.spec['bindings']['score']['outputs']
        self.helper('development_select_score',bindings._entry(
            {'condition':'bit',**{'new_'+k:t for k,t in score_types.items()},**{'old_'+k:t for k,t in score_types.items()}},
            score_types,{k:c.choose(V('condition'),V('new_'+k),V('old_'+k)) for k in score_types},
            'Select the matching accepted-program score and next witness.',[c.bit_guard(V('condition'))]))
        self.meta['helpers'] = {name:name for name in self.g['functions'] if name.startswith('development_')}

    def mutation(self):
        nodes = self.g['mutation']['nodes']
        old = {k:state(v) for k,v in PROGRAM_FIELDS.items()}
        proposal = self.call('development_old_mutator_proposal','propose_edit',{
            'witness_x':state(DIAGNOSTIC_FIELDS['witness_x']), 'witness_y':state(DIAGNOSTIC_FIELDS['witness_y']),
            'witness_distance':state(DIAGNOSTIC_FIELDS['witness_distance']), 'node_count':old['node_count'],
            'quota':state(DIAGNOSTIC_FIELDS['quota']), 'control':ref('mutation_mutation_body_2','control'),
            'ar':state('ar'),'field_distance':ref('mutation_mutation_field_role0_8','distance'),
            'target_field':ref('mutation_target_field_role0_9','distance')},nodes=nodes,mutation=True)
        encoded = self.pure('development_mutation_descriptor','development_descriptor_encode',{
            'source_index':{'target_index':True},**proposal,'enabled':state(DIAGNOSTIC_FIELDS['enabled']),
            'revision':old['revision'],**{f'old_{i}':ref('mutation_target_body_1',f'reserved_{i}') for i in range(5)}},
            [f'reserved_{i}' for i in range(5)],nodes=nodes)
        self.g['mutation']['returns'].update(encoded)

    def action(self):
        # The first source action phase already executes the published Klein
        # and PSI. One same-record situated context is shared by protected
        # resource roles during this phase; their domain metric stays separate.
        self.nodes.append({'id':'development_resource_record','op':'read_record','record':{'key':RECORD_KEY},
            'bank':'published','fields':['anchor_u','anchor_v','anchor_orientation','radius',*[f'reserved_{i}' for i in range(5)]]})
        self.nodes.append({'id':'development_resource_placement','op':'call_record','record':{'key':RECORD_KEY},
            'bank':'published','slot':'placement','role':0,
            'args':{a:ref('development_resource_record',b) for a,b in [('u','anchor_u'),('v','anchor_v'),('orientation','anchor_orientation')]}})
        self.pure('development_resource_nearest','nearest_klein_lift',{
            'query_u':ref('action_operator_mutation_klein_body_role0_8','ku'),
            'query_v':ref('action_operator_mutation_klein_body_role0_8','kv'),
            **{a:ref('development_resource_placement',b) for a,b in [('anchor_u','u'),('anchor_v','v'),('anchor_orientation','orientation')]}},
            ['dx','dy','anchor_frame_y'])
        self.nodes.append({'id':'development_resource_field','op':'call_record','record':{'key':RECORD_KEY},
            'bank':'published','slot':'field','role':0,'args':{'dx':ref('development_resource_nearest','dx'),
                'dy':ref('development_resource_nearest','dy'),'radius':ref('development_resource_record','radius')}})
        old = {k:state(v) for k,v in PROGRAM_FIELDS.items()}
        code,geometry = self.validate('development_live',old)
        self.pure('development_live_guard','development_require_live',{'code':code,'geometry':geometry,
            'query_x':state(DIAGNOSTIC_FIELDS['query_x']),'query_y':state(DIAGNOSTIC_FIELDS['query_y']),
            'enabled':state(DIAGNOSTIC_FIELDS['enabled'])},['valid'])
        # Score incumbent first, so its temporary sample values can die before
        # candidate construction and keep the fixed frame bound manageable.
        old_score = self.score('development_old',old)
        descriptor = self.pure('development_published_descriptor','development_descriptor_decode',
            {f'reserved_{i}':ref('development_resource_record',f'reserved_{i}') for i in range(5)},('x','y','half','valid'))
        candidate = self.call('development_construct_code','construct_code',
            {**{k:old[k] for k in bindings.HEADER_NAMES+bindings.CODE_NAMES},'valid':descriptor['valid']})
        candidate.update(self.call('development_construct_boxes','construct_boxes',
            {**{k:old[k] for k in bindings.BOX_NAMES},'node_count':old['node_count'],**descriptor}))
        code,geometry = self.validate('development_candidate',candidate)
        valid = self.pure('development_candidate_guard','development_candidate_valid',
            {'code':code,'geometry':geometry,'proposed':descriptor['valid']},['valid'])['valid']
        safe = self.select_program('development_safe',valid,candidate,old)
        candidate_score = self.score('development_candidate',safe)
        acceptance = self.call('development_accept','accept',{'old_score':old_score['score'],
            'candidate_score':candidate_score['score'],'valid':valid})
        accepted = self.select_program('development_retained',acceptance['accepted'],safe,old)
        # Selecting matching score/witness results avoids a third training
        # evaluation while preserving the exact accepted-program consequence.
        score = self.pure('development_retained_score','development_select_score',
            {'condition':acceptance['accepted'],**{'new_'+k:v for k,v in candidate_score.items()},
             **{'old_'+k:v for k,v in old_score.items()}},old_score)
        distance = self.distance('development_query',accepted,state(DIAGNOSTIC_FIELDS['query_x']),state(DIAGNOSTIC_FIELDS['query_y']))
        diagnostics = self.pure('development_final_diagnostics','development_diagnostics',
            {'distance':distance,'trials':state(DIAGNOSTIC_FIELDS['trials'])},['admitted','trials'])
        self.g['returns'].update({PROGRAM_FIELDS[k]:v for k,v in accepted.items()})
        fields = {**score, **acceptance, **diagnostics,'distance':distance,'previous_score':old_score['score']}
        self.g['returns'].update({DIAGNOSTIC_FIELDS[k]:fields[k] if k in fields else state(DIAGNOSTIC_FIELDS[k])
                                  for k in DIAGNOSTIC_FIELDS})
        self.meta['helpers'] = {name:name for name in self.g['functions'] if name.startswith('development_')}
        self.meta['publication'] = {'descriptor':'old-snapshot record mutation before action',
            'program':'candidate constructed and evaluated in action; accepted words published atomically with the entire returned state',
            'diagnostics':'query distance/admission and selected score/witness describe the returned accepted program'}


def build_definition(model, cycle, spec, instance_count=17, *, graph=None):
    program,quota,query = validate_spec(spec)
    if model['operators'][-1]['key'] != RECORD_KEY or model['operators'][-1]['index'] != SOURCE_INDEX:
        raise ValueError('Development requires its explicitly declared resource record at source index31')
    definition = author.build_definition(model,cycle,instance_count)
    definition['profile'] = resident.PROFILE
    extra = {PROGRAM_FIELDS[k]:bindings.PROGRAM_TYPES[k] for k in PROGRAM_FIELDS}
    extra.update({DIAGNOSTIC_FIELDS[k]:v for k,v in DIAGNOSTIC_TYPES.items()})
    definition['state_names'].extend(extra)
    initial_words = bindings.pack_program(program)
    for instance in definition['instances']:
        instance['state'].update({PROGRAM_FIELDS[k]:v for k,v in initial_words.items()})
        instance['state'].update(dict.fromkeys(DIAGNOSTIC_FIELDS.values(),0))
        instance['state'].update({DIAGNOSTIC_FIELDS['query_x']:query[0], DIAGNOSTIC_FIELDS['query_y']:query[1],
                                  DIAGNOSTIC_FIELDS['quota']:quota,DIAGNOSTIC_FIELDS['enabled']:spec['initial']['enabled']})
    family = definition['records'][-1]['body']
    contracts, roles, functions = {}, {}, {}
    for i,(name,entry) in enumerate(spec['bindings'].items()):
        function_name = 'development__'+name
        definition['functions'][function_name] = {'signature':1000+i,'binding':deepcopy(entry['binding'])}
        contracts[function_name] = {k:deepcopy(entry[k]) for k in ('inputs','outputs')}
        functions[name] = function_name
        if name == 'propose_edit':
            for mutator in ('mutation','mutation_successor'):
                definition['families'][mutator]['methods']['2'] = function_name
        else:
            roles[name] = 200+i
            definition['families'][family]['methods'][str(200+i)] = function_name
    definition['source']['graph_type_contracts'] = {'profile':nominal.EXTENDED_TYPE_PROFILE,'states':extra,'functions':contracts}
    metadata = {'profile':PROFILE,'record_key':RECORD_KEY,'source_index':SOURCE_INDEX,'record_ordinal':31,
        'family':family,'roles':roles,'functions':functions,'mutator_role':2,
        'program_state_fields':deepcopy(PROGRAM_FIELDS),'diagnostic_state_fields':deepcopy(DIAGNOSTIC_FIELDS),
        'descriptor_fields':dict(zip(('x','y','half','valid','reserved'),(f'reserved_{i}' for i in range(5)))),
        'protected':deepcopy(spec['protected']),'policy':deepcopy(spec['policy']),
        'training_points':deepcopy(spec['training_points']),'source':deepcopy(spec),
        'source_sha256':ir.sha256(ir.json_bytes(spec)),
        'construction_scope':'Resident generation of canonical BOX/SEPARATED_UNION program words in mutable state; fixed interpreter and bounded grammar.',
        'actor_boundary':'AI authors domain, grammar, objective and metarules before compilation; resident calls construct, evaluate and retain program data without a host decision per epoch.'}
    definition['source']['development'] = metadata
    if graph is None:
        graph = ir.read_json(ROOT/'source_bindings/graphs/amplitude_v0.1.json')[0]
        # The template owns source edges, not native tape/register positions.
        graph = json.loads(json.dumps(graph).replace('amplitude_budget',RECORD_KEY))
        graph['type_profile'] = nominal.EXTENDED_TYPE_PROFILE
        graph['source'] = {'edition':PROFILE,'base_graph':'source_bindings/graphs/amplitude_v0.1.json',
                           'development_source_sha256':metadata['source_sha256']}
        graph['meaning'] = 'Complete source recurrence with resident construction and retention of resource-distance program data.'
        builder = DevelopmentGraph(definition,graph,spec,metadata)
        builder.install_helpers()
        builder.mutation()
        builder.action()
    else:
        graph = deepcopy(graph)
        helper_graph = {'functions':{},'phases':[{'nodes':[]}]}
        helper_metadata = {'roles':roles}
        DevelopmentGraph(definition,helper_graph,spec,helper_metadata).install_helpers()
        for name,entry in helper_graph['functions'].items():
            if not resident.same_structure(graph.get('functions',{}).get(name),entry):
                raise ValueError('Missing or modified protected development helper: '+name)
        metadata['helpers'] = helper_metadata['helpers']
        metadata['publication'] = {'descriptor':'old-snapshot record mutation before action',
            'program':'candidate constructed and evaluated in action; accepted words published atomically with the entire returned state',
            'diagnostics':'query distance/admission and selected score/witness describe the returned accepted program'}
    graph_compiler.apply_graph(definition,cycle,graph,resident_backend=resident)
    definition['source']['development']['graph_sha256'] = ir.sha256(ir.json_bytes(graph))
    definition['source']['development']['structural_fidelity'] = development_fidelity.audit_development_graph(definition,cycle,graph)
    definition['source']['development']['fidelity_checker_sha256'] = ir.sha256(Path(development_fidelity.__file__).read_bytes())
    return definition,graph


def compile_program(model,cycle,spec,instance_count=17,*,graph=None):
    definition,graph = build_definition(model,cycle,spec,instance_count,graph=graph)
    raw,manifest = resident.compile_definition(model,definition)
    manifest['binding_contract']['development'] = deepcopy(definition['source']['development'])
    manifest['development_profile'] = PROFILE
    manifest['scope'] = 'Source-connected bounded resident SDF construction; execution evidence recorded separately.'
    return definition,graph,raw,manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    p = commands.add_parser('compile')
    p.add_argument('--source',type=Path)
    p.add_argument('--model',type=Path)
    p.add_argument('--cycle',type=Path,default=cycle_binding.CYCLE)
    p.add_argument('--graph',type=Path)
    p.add_argument('--instances',type=int,default=17)
    p.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(argv)
    spec = ir.read_json(args.source)[0] if args.source else make_spec()
    model = ir.read_json(args.model)[0] if args.model else make_model()
    cycle = ir.read_json(args.cycle)[0]
    graph = ir.read_json(args.graph)[0] if args.graph else None
    definition,graph,raw,manifest = compile_program(model,cycle,spec,args.instances,graph=graph)
    files = {'source_model.json':ir.json_bytes(model),'source_cycle.json':ir.json_bytes(cycle),
             'development_source.json':ir.json_bytes(spec),'source_graph.json':ir.json_bytes(graph),
             'definition.json':ir.json_bytes(definition),'program.bin':raw}
    for module in (sys.modules[__name__],bindings,sdf,graph_compiler,nominal,resident,ir,author,
                   development_fidelity,cycle_binding,author.slots,author.catalogue,author.enzyme):
        path = Path(module.__file__)
        files['compiler/'+path.name] = path.read_bytes()
    for name in ('source_ir.py','source_graph_fidelity.py','source_development_results.py'):
        files['compiler/'+name] = Path(__file__).with_name(name).read_bytes()
    manifest['files'] = {name:{'bytes':len(data),'sha256':ir.sha256(data)} for name,data in files.items()}
    args.output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        path = args.output/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    (args.output/'manifest.json').write_bytes(ir.json_bytes(manifest))
    print(json.dumps({'profile':PROFILE,'output':str(args.output.resolve()),'instances':args.instances,
        'state_width':len(definition['state_names']),'mutation_steps':len(definition['mutation_plan']),
        'action_steps':len(definition['action_plan']),'program_sha256':ir.sha256(raw)},indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError,OverflowError,RecursionError) as error:
        print(f'{type(error).__name__}: {error}',file=sys.stderr)
        raise SystemExit(1)
