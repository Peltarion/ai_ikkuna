import torch
import numpy as np

from ikkuna.export.subscriber import PlotSubscriber, SynchronizedSubscription
from ikkuna.export.messages import get_default_bus

ZERO_TENSOR = torch.tensor(0.0).cuda()


class RatioSubscriber(PlotSubscriber):
    '''A :class:`~ikkuna.export.subscriber.Subscriber` which computes the average ratio between two
    quantities.  The dividend will be the first element of the
    :attr:`~ikkuna.export.subscriber.Subscription.kinds` property, the divisor the second.
    Therefore it is vital to pass the message kinds to the
    :class:`~ikkuna.export.subscriber.Subscription` object in the correct order.'''

    def __init__(self, kinds, message_bus=get_default_bus(), tag=None, subsample=1, ylims=None,
                 backend='tb', absolute=True, **tbx_params):
        '''
        Parameters
        ----------
        absolute :  bool
                    Whether to use absolute ratio
        '''
        if len(kinds) != 2:
            raise ValueError(f'RatioSubscriber requires 2 kinds, got {len(kinds)}.')

        title        = f'{kinds[0]}/{kinds[1]} ratio'
        ylabel       = 'Ratio'
        xlabel       = 'Train step'
        subscription = SynchronizedSubscription(self, kinds, tag, subsample)
        super().__init__(subscription, message_bus,
                         {'title': title,
                          'ylabel': ylabel,
                          'ylims': ylims,
                          'xlabel': xlabel},
                         backend=backend, **tbx_params)
        if absolute:
            self._metric_postprocess = torch.abs
        else:
            self._metric_postprocess = lambda x: x

    def compute(self, message_bundle):
        '''The ratio between the two kinds is computed as the ratio of L2-Norms of the two Tensors.
        A :class:`~ikkuna.export.messages.SubscriberMessage` with the identifier
        ``{kind1}_{kind2}_ratio`` is published.'''

        module_name = message_bundle.identifier

        dividend    = message_bundle.data[self._subscription.kinds[0]]
        divisor     = message_bundle.data[self._subscription.kinds[1]]

        scale1      = dividend.norm()
        scale2      = divisor.norm()
        ratio       = (scale1 / scale2).item()

        self._backend.add_data(module_name, ratio, message_bundle.seq)

        kind = f'{self._subscription.kinds[0]}_{self._subscription.kinds[1]}_ratio'
        self.message_bus.publish_subscriber_message(message_bundle.seq, message_bundle.step,
                                                    message_bundle.epoch, kind,
                                                    message_bundle.identifier, ratio)
