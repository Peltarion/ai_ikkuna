from ikkuna.export.subscriber import PlotSubscriber, SynchronizedSubscription
from ikkuna.export.messages import get_default_bus


class TrainAccuracySubscriber(PlotSubscriber):
    ''':class:`~ikkuna.export.subscriber.Subscriber` which computes the batch accuracy.'''

    def __init__(self, message_bus=get_default_bus(), tag=None, subsample=1, ylims=None,
                 backend='tb', **tbx_params):
        '''
        For parameters see :class:`~ikkuna.export.subscriber.PlotSubscriber`
        '''
        subscription = SynchronizedSubscription(self, ['network_output', 'input_labels'], tag,
                                                subsample)

        title  = f'Train batch accuracy'
        xlabel = 'Step'
        ylabel = 'Accuracy'
        super().__init__(subscription,
                         message_bus,
                         {'title': title, 'xlabel': xlabel, 'ylims': ylims, 'ylabel': ylabel},
                         backend=backend, **tbx_params)

    def compute(self, message_bundle):
        Y           = message_bundle.data['network_output']
        labels      = message_bundle.data['input_labels']
        predictions = Y.argmax(1)
        n_correct   = (predictions == labels).sum().item()
        accuracy    = n_correct / float(labels.numel())
        self._backend.add_data('Train batch accuracy', accuracy, message_bundle.seq)
