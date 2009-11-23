import datetime

from zope import component, schema
from zope.interface.common.idatetime import ITZInfo
from zope.security.checker import canAccess, canWrite
from zope.security.interfaces import IGroup
import zope.app.form.interfaces
import zope.app.pagetemplate
import zope.publisher.browser
import zope.formlib.namedtemplate

from zope.app.security.interfaces import IAuthentication

from zope.locking import interfaces
import zc.i18n.date
import zc.i18n.duration

from zope.locking.i18n import _

UNAVAILABLE = _('This action is unavailable now')
ERROR = _('Bad expiration date value')

class ManageTokenView(zope.publisher.browser.BrowserPage):

    prefix="manage_tokens"

    expiration_changed = False

    def update(self):
        self.broker = broker = interfaces.ITokenBroker(self.context, None)
        # doLock, doLockShared, doLockJoin,  doFreeze, doRelease,
        # doChangeExpiration, doEnd
        if broker is not None:
            token = broker.get()
            form = self.request
            if self.prefix + '.doLock' in form:
                if token is not None:
                    self.message = UNAVAILABLE
                else:
                    broker.lock()
            elif self.prefix + '.doLockShared' in form:
                if token is not None:
                    self.message = UNAVAILABLE
                else:
                    broker.lockShared()
            elif self.prefix + '.doFreeze' in form:
                if token is not None:
                    self.message = UNAVAILABLE
                else:
                    broker.freeze()
            elif token is None:
                self.message = UNAVAILABLE
            else:
                handler = interfaces.ITokenHandler(token, None)
                if self.prefix + '.doLockJoin' in form:
                    if (handler is None or
                        not interfaces.ISharedLock.providedBy(token)):
                        self.message = UNAVAILABLE
                    else:
                        handler.join()
                if self.prefix + '.doRelease' in form:
                    if handler is None:
                        self.message = UNAVAILABLE
                    else:
                        handler.release()
                if self.prefix + '.doEnd' in form:
                    token.end()
                if self.prefix + '.doChangeExpiration' in form:
                    field = schema.Datetime(
                        __name__='expiration',
                        title=_('Expiration'),
                        required=False)
                    widget = component.getMultiAdapter(
                        (field, self.request),
                        zope.app.form.interfaces.IInputWidget)
                    widget.setPrefix(self.prefix + '.widget')
                    if widget.hasValidInput():
                        new = widget.getInputValue()
                        if new is not None:
                            new = zc.i18n.date.normalize(self.request, new)
                        if canWrite(token, 'expiration'):
                            token.expiration = new
                        else:
                            handler.expiration = new
                        self.expiration_changed = True
                    elif widget.hasInput():
                        self.message = ERROR # TODO: use widget error

    def __call__(self):
        self.update()
        return self.render()

    def render(self):
        tzinfo = ITZInfo(self.request)
        self.now = zc.i18n.date.format(
            self.request,
            datetime.datetime.now(tzinfo))
        broker = self.broker
        if broker is not None:
            self.canLock = canAccess(broker, 'lock')
            self.canLockShared = canAccess(broker, 'lockShared')
            self.canFreeze = canAccess(broker, 'freeze')
            self.token = token = broker.get()
            if token is not None:
                self.started = zc.i18n.date.format(
                    self.request,
                    token.started.astimezone(tzinfo))
                self.othersInToken = self.inToken = False
                self.participants = []
                principals = component.getUtility(IAuthentication)
                ct = len(list(token.principal_ids))
                self.noParticipants = ct == 0
                self.singleParticipant = ct == 1
                self.multiParticipants = ct > 1
                for p in token.principal_ids:
                    info = {}
                    info['principal'] = principal = principals.getPrincipal(p)
                    info['isGroup'] = IGroup.providedBy(principal)
                    if p == self.request.principal.id:
                        self.inToken = True
                        info['isRequestPrincipal'] = True
                    else:
                        self.othersInToken = True
                        info['isRequestPrincipal'] = False
                    self.participants.append(info)
                self.isEndable = interfaces.IEndable.providedBy(token)
                self.isExclusiveLock = interfaces.IExclusiveLock.providedBy(
                    token)
                self.isSharedLock = interfaces.ISharedLock.providedBy(token)
                self.isFreeze = (interfaces.IFreeze.providedBy(token) and not
                                 self.isEndable)
                self.isEndableFreeze = interfaces.IEndableFreeze.providedBy(
                    token)
                if self.isEndable:
                    self.canEnd = canAccess(token, 'end')
                    self.expiring = token.expiration is not None
                    if self.expiring:
                        self.expiration = zc.i18n.date.format(
                            self.request,
                            token.expiration.astimezone(tzinfo))
                        self.remaining_duration = zc.i18n.duration.format(
                            self.request,
                            token.remaining_duration)
                        self.duration = zc.i18n.duration.format(
                            self.request,
                            token.duration)
                    self.handler = handler = interfaces.ITokenHandler(
                        token, None)
                    if (canWrite(token, 'expiration') or
                        (handler is not None and
                         canWrite(handler, 'expiration') and
                         self.inToken)):
                        # get an editable expiration field
                        field = schema.Datetime(
                            __name__='expiration',
                            title=_('Expiration'),
                            required=False)
                        self.widget = widget = component.getMultiAdapter(
                            (field, self.request),
                            zope.app.form.interfaces.IInputWidget)
                        widget.setPrefix(self.prefix + '.widget')
                        if self.expiration_changed or not widget.hasInput():
                            widget.setRenderedValue(token.expiration)
                    if handler is not None:
                        self.canRelease = self.inToken and canAccess(
                            handler, 'release')
                        if self.isSharedLock:
                            self.canJoin = not self.inToken and canAccess(
                                handler, 'join')
                            self.canAdd = self.inToken and canAccess(
                                handler, 'add')
        return self.template()

    template = zope.formlib.namedtemplate.NamedTemplate('default')

defaultTemplate = zope.formlib.namedtemplate.NamedTemplateImplementation(
    zope.app.pagetemplate.ViewPageTemplateFile('tokenview.pt'),
    ManageTokenView)
