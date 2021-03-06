import theano
import theano.tensor as T
import numpy as np

from util import *
from layer import *
from graph_state import GraphState, GraphStateSpec

class AggregateRepresentationTransformation( object ):
    """
    Transforms a graph state into a single representation vector
    """
    def __init__(self, representation_width, graph_spec, dropout_keep=1, dropout_output=True):
        self._representation_width = representation_width
        self._graph_spec = graph_spec

        self._representation_stack = LayerStack(graph_spec.num_node_ids + graph_spec.node_state_size, representation_width+1, name="aggregaterepr", dropout_keep=dropout_keep, dropout_input=False, dropout_output=dropout_output)
        
    @property
    def params(self):
        return self._representation_stack.params

    def dropout_masks(self, srng):
        return self._representation_stack.dropout_masks(srng)

    def process(self, gstate, dropout_masks=Ellipsis):
        """
        Convert the graph state to a representation vector, using sigmoid attention to scale representations

        Params:
            gstate: A GraphState giving the current state

        Returns: A representation vector of shape (n_batch, representation_width)
        """
        if dropout_masks is Ellipsis:
            dropout_masks = None
            append_masks = False
        else:
            append_masks = True

        flat_obs = T.concatenate([
                        gstate.node_ids.reshape([-1, self._graph_spec.num_node_ids]),
                        gstate.node_states.reshape([-1, self._graph_spec.node_state_size])], 1)
        flat_activations, dropout_masks = self._representation_stack.process(flat_obs, dropout_masks)
        activations = flat_activations.reshape([gstate.n_batch, gstate.n_nodes, self._representation_width+1])

        activation_strengths = activations[:,:,0]
        selector = T.shape_padright(T.nnet.sigmoid(activation_strengths) * gstate.node_strengths)
        representations = T.tanh(activations[:,:,1:])

        result = T.tanh(T.sum(selector * representations, 1))
        if append_masks:
            return result, dropout_masks
        else:
            return result




