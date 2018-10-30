import torch
import numpy as np

from ikkuna.export.subscriber import PlotSubscriber, SynchronizedSubscription


class VarianceSubscriber(PlotSubscriber):
    '''A :class:`~ikkuna.export.subscriber.Subscriber` which computes the
    variance of quantity for the current batch.
    '''

    def __init__(self, kinds, tag=None, subsample=1, ylims=None, backend='tb', **tbx_params):
        title        = f'variance of {kinds[0]}'
        ylabel       = 'σ^2'
        xlabel       = 'Train step'
        subscription = SynchronizedSubscription(self, kinds, tag, subsample)
        super().__init__(subscription, {'title': title,
                                        'ylabel': ylabel,
                                        'ylims': ylims,
                                        'xlabel': xlabel},
                         backend=backend, **tbx_params)

    def compute(self, message_bundle):

        module_name  = message_bundle.identifier

        data = message_bundle.data[self._subscription.kinds[0]]
        var = data.var()
        self._backend.add_data(module_name, var, message_bundle.seq)
