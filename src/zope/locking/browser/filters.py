import persistent.interfaces
from zope import component, interface
import zope.publisher.interfaces.browser
from zope.locking import interfaces

@component.adapter(
    interface.Interface, zope.publisher.interfaces.browser.IBrowserRequest)
def locked(context, request):
    if persistent.interfaces.IPersistent.providedBy(context):
        utility = component.queryUtility(interfaces.ITokenUtility)
        if utility:
            token = utility.get(context)
            if token and request.principal.id in frozenset(token.principal_ids):
                return True
    return False

@component.adapter(
    interface.Interface, zope.publisher.interfaces.browser.IBrowserRequest)
def lockedOut(context, request):
    if persistent.interfaces.IPersistent.providedBy(context):
        utility = component.queryUtility(interfaces.ITokenUtility)
        if utility:
            token = utility.get(context)
            if (token and
                request.principal.id not in frozenset(token.principal_ids)):
                return True
    return False
