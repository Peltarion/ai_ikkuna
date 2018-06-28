import re
import torch
from collections import defaultdict

from ikkuna.export.messages import NetworkData

NUMBER_REGEX = re.compile(r'\d+')


class Exporter(object):
    '''Class for managing publishing of data from model code.

    An :class:`Exporter` is used in the model code by either explicitly registering modules for
    tracking with :meth:`Exporter.add_modules` or by calling it with newly constructed modules
    which will then be returned as-is, but be registered in the process.

    .. code-block:: python

        e = Exporter(...)
        features = nn.Sequential([
            nn.Linear(...),
            e(nn.Conv2d(...)),
            nn.ReLU()
        ])

    No further changes to the model code are necessary, but for certain visualizations, the
    exporter requires access to the model in its entirety, so :meth:`Exporter.add_model` should be
    used.

    Attributes
    ----------
    _modules    :   list
                    All tracked modules
    _layer_counter  :   defaultdict
                        Dictionary tracking number and kind of added modules for
                        generating a name for each.
    _layer_names    :   list
                        List which parallels _modules and contains the label for each
    _weight_cache   :   dict
                        Cache for keeping the previous weights for computing differences
    _bias_cache :   dict
    '''

    def __init__(self, frequency=1):
        '''Create a new ``Exporter``.

        Parameters
        ----------
        frequency   :   int
                        Number of training steps to pass by before publishing a new update.
        '''
        self._modules            = []
        self._frequency          = frequency
        self._layer_counter      = defaultdict(int)
        self._layer_names        = []
        self._weight_cache       = {}     # expensive :(
        self._bias_cache         = {}
        self._subscriptions      = set()
        self._activation_counter = defaultdict(int)
        self._gradient_counter   = defaultdict(int)
        self._model              = None
        self._train_step         = 0
        self._epoch              = 0
        self._global_step        = 0
        self._is_training        = True

    def _check_model(self):
        if not self._model:
            import sys
            print('Warning: No model set. This will either do nothing or crash.', file=sys.stderr)

    def subscribe(self, subscription):
        '''Add a subscriber function or a callable for a certain event. The signature should be

        .. py:function:: callback(data: NetworkData)

        Parameters
        ----------
        subscription    :   ikkuna.export.subscriber.Subscription
                            Subscription to register
        '''
        self._subscriptions.add(subscription)

    def get_or_make_label(self, module):
        '''Create or retrieve the label for a module. If the module is already tracked, its label
        is returned, else a new one is created.

        Parameters
        ----------
        module  :   torch.nn.Module

        Returns
        -------
        str
        '''
        if module not in self._modules:
            layer_kind = module.__class__.__name__
            number     = self._layer_counter[layer_kind]
            layer_name = f'{layer_kind}-{number}'
        else:
            index      = self._modules.index(module)
            layer_name = self._layer_names[index]
        self._layer_counter[module.__class__.__name__] += 1
        return layer_name

    def _add_module(self, name, module):
        if module not in self._modules:
            self._layer_names.append(name)
            self._modules.append(module)
            module.register_forward_hook(self.new_activations)
            module.register_backward_hook(self.new_gradients)

    def add_modules(self, module):
        '''Add modules to supervise. Currently, only activations and gradients are tracked. If the
        module has ``weight`` and/or ``bias`` members, updates to those will be tracked.
        The method will recursively add all children of a :class:`torch.nn.Sequential` module. Other
        containers are currently unsupported in will result in activations and gradients being
        tracked for the module as one.

        Parameters
        ----------
        module  :   tuple(str, torch.nn.Module) or torch.nn.Module

        Raises
        ------
        ValueError
            If ``module`` is neither a tuple, nor a (subclass of) :class:`torch.nn.Module`
        '''
        if isinstance(module, tuple):   # name already given -> use that
            layer_name, module = module
            self._add_module(layer_name, module)
            return module
        elif isinstance(module, torch.nn.Module):
            # if sequential module, recursively add children. generate names or take given names
            if isinstance(module, torch.nn.Sequential):
                named_children = module.named_children()
                for name, mod in named_children:
                    # the nn.Sequential module adds its children with str(index) names in the
                    # absence of a given name. Therefore we assume that if we see such names, they
                    # were not user-selected and can be overridden with more descriptive ones
                    if re.match(NUMBER_REGEX, name):
                        self.add_modules(mod)
                    else:
                        self.add_modules((name, mod))
                return module
            else:
                layer_name = self.get_or_make_label(module)
                self._add_module(layer_name, module)
                return module
        else:
            raise ValueError(f'Don\'t know how to handle {module.__class__.__name__}')

    def __call__(self, *args):
        # TODO: Handle initialization methods torch.nn.Sequential with named modules
        if all(map(lambda o: isinstance(o, torch.nn.Module), args)):
            return self.add_modules(*args)
        elif len(args) == 1 and isinstance(args[0], torch.optim.Optimizer):
            return self.add_optimizer(args[0])

    def publish(self, module, kind, data):
        '''Publish an update to all registered subscribers.

        Parameters
        ----------
        module  :   torch.nn.Module
                    The module in question
        kind    :   str
                    Kind of subscriber to notify
        data    :   torch.Tensor
                    Payload
        '''
        self._check_model()
        for sub in self._subscriptions:
            msg = NetworkData(seq=self._global_step, tag=None, kind=kind,
                              module=self.get_or_make_label(module), step=self._train_step,
                              epoch=self._epoch, payload=data)
            sub(msg)

    def train(self, train=True):
        self._is_training = train

    def test(self, test=True):
        self.train(not test)

    def export(self, kind, module, data):
        '''Publish new data to any subscribers.

        Parameters
        ----------
        kind    :   str
                    Kind of subscription
        module  :   torch.nn.Module
        data    :   torch.Tensor
                    Payload to publish
        '''
        if len(self._subscriptions) == 0:
            pass
        else:
            self.publish(module, kind, data)

    def new_activations(self, module, in_, out_):
        '''Callback for newly arriving activations. Registered as a hook to the tracked modules.
        Will trigger exportation of all new activation and weight/bias data.

        Parameters
        ----------
        module  :   torch.nn.Module
        in_ :   torch.Tensor
                Dunno what this is
        out_    :   torch.Tensor
                    The new activations
        '''
        if not self._is_training:
            return
        self._activation_counter[module] += 1
        if hasattr(module, 'weight'):
            if module in self._weight_cache:
                self.export('weight_updates', module, module.weight - self._weight_cache[module])
            else:
                self.export('weight_updates', module, torch.zeros_like(module.weight))
            self.export('weights', module, module.weight)
            self._weight_cache[module] = torch.tensor(module.weight)
        if hasattr(module, 'bias') and module.bias is not None:   # bias can be present, but be None
            # in the first train step, there can be no updates, so we just publish zeros, otherwise
            # clients would error out since they don't receive the expected messages
            if module in self._bias_cache:
                self.export('bias_updates', module, module.bias - self._bias_cache[module])
            else:
                self.export('bias_updates', module, torch.zeros_like(module.bias))
            self.export('biases', module, module.bias)
            self._bias_cache[module] = torch.tensor(module.bias)
        self.export('activations', module, out_)

    def new_gradients(self, module, in_, out_):
        '''Callback for newly arriving gradients. Registered as a hook to the tracked modules.
        Will trigger exportation of all new gradient data.

        Parameters
        ----------
        module  :   torch.nn.Module
        in_ :   torch.Tensor
                Dunno what this is
        out_    :   torch.Tensor
                    The new activations
        '''
        if not self._is_training:
            return
        self._gradient_counter[module] += 1
        if isinstance(out_, tuple):
            if len(out_) > 1:
                raise RuntimeError(f'Not sure what to do with tuple gradients.')
            else:
                out_, = out_
        self.export('gradients', module, out_)

    def set_model(self, model):
        '''Set the model for direct access for some metrics.

        Parameters
        ----------
        model   :   torch.nn.Module
        '''
        self._model = model
        from types import MethodType
        #############################################
        #  Patch the train function to notify self  #
        #############################################
        train_fn = model.train

        def new_train_fn(this, mode=True):
            train_fn(mode=mode)
            self._is_training = mode
        model.train = MethodType(new_train_fn, model)

        #########################################################
        #  Patch forward function to step() self automatically  #
        #########################################################
        forward_fn = model.forward

        def new_forward_fn(this, *args):
            self.step()     # we need to step first, else act and grads get different steps
            ret = forward_fn(*args)
            return ret
        model.forward = MethodType(new_forward_fn, model)

    def step(self):
        '''Increase batch counter (per epoch) and the global step counter.'''
        self._train_step  += 1
        self._global_step += 1

    def epoch_finished(self):
        '''Increase the epoch counter and reset the batch counter.'''
        for sub in self._subscriptions:
            sub.epoch_finished(self._epoch)
        self._epoch      += 1
        self._train_step = 0
