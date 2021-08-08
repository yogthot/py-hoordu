from .common import *
from ..config import *
from ..models import *

class APIError(Exception):
    pass

class SearchDetails:
    def __init__(self, hint=None, title=None, description=None, thumbnail_url=None, related_urls=set()):
        self.hint = hint
        self.title = title
        self.description = description
        self.thumbnail_url = thumbnail_url
        self.related_urls = set(related_urls)

class IteratorBase:
    def __init__(self, plugin, subscription=None, options=None):
        self.plugin = plugin
        self.subscription = subscription
        
        if self.subscription is not None:
            self.options = Dynamic.from_json(self.subscription.options)
            self.state = Dynamic.from_json(self.subscription.state)
        else:
            self.options = options
            self.state = Dynamic()
    
    def init(self):
        """
        Override this method to implement any startup IO related
        to this specific subscription that doesn't need to execute
        on every fetch call.
        """
        
        pass
    
    def fetch(self, direction=FetchDirection.newer, n=None):
        """
        Try to get at least `n` newer or older posts from this search
        depending on the direction.
        Create a RemotePost entry and any associated Files for each post found,
        thumbnails should be downloaded, files are optional.
        Posts should always come ordered in the same way.
        
        Returns a list of the new RemotePost objects.
        """
        
        raise NotImplementedError

class PluginBase:
    name = None
    version = 0
    required_hoordu = '0.0.0'
    
    iterator = None
    
    @classmethod
    def config_form(cls):
        """
        Returns a form for the configuration of the values by the plugin.
        """
        
        raise NotImplementedError
    
    @classmethod
    def init(cls, core, parameters=None):
        """
        Tries to initialize a plugin from existing configuration or new configuration
        passed in `parameters`.
        
        If the plugin initializes successfully, this should return a tuple of
        True and the plugin object.
        Otherwise, it should return a tuple of False and a form for any missing values
        required (e.g.: oauth tokens).
        """
        
        raise NotImplementedError
    
    @classmethod
    def update(cls, core):
        """
        Updates the database objects related to this plugin/source, if needed.
        """
        
        pass
    
    def __init__(self, core, config=None):
        self.core = core
        self.source = core.source
        self.log = core.logger
        self.session = core.session
        
        self.config = config
        if self.config is None:
            self.config = Dynamic.from_json(self.source.config)
    
    def commit(self):
        self.core.commit()
    
    def parse_url(self, url):
        """
        Checks if an url can be downloaded by this plugin.
        
        Returns the remote id if the url corresponds to a single post,
        a Dynamic object that can be passed to search if the url
        corresponds to multiple posts, or None if this plugin can't
        download or create a search with this url.
        """
        
        return None
        
    def download(self, id=None, remote_post=None, preview=False):
        """
        Creates or updates a RemotePost entry along with all the associated Files,
        and downloads all files and thumbnails that aren't present yet.
        
        If remote_post is passed, its original_id will be used and it will be
        updated in place.
        
        If preview is set to True, then only the thumbnails are downloaded.
        
        Returns the downloaded RemotePost object.
        """
        
        raise NotImplementedError
    
    def search_form(self):
        """
        Returns the form or a list of forms used for searches and subscriptions.
        (e.g.: user id, a search string, or advanced options available on the website)
        """
        
        return None
    
    def get_search_details(self, options):
        """
        Returns a SearchDetails object with extra details about the search that would
        be performed by this set of options (e.g.: user timeline).
        May return None if no specific information is found (e.g.: global searches).
        """
        
        return None
    
    def search(self, options):
        """
        Creates a temporary search for a given set of search options.
        
        Returns a post iterator object.
        """
        
        if self.iterator is None:
            raise NotImplementedError
        
        options = Dynamic.from_json(options)
        
        return self.iterator(self, options=options)
    
    def subscription_repr(self, options):
        """
        Returns a simple representation of the subscription, used to find duplicate
        subscriptions.
        """
        
        raise NotImplementedError
    
    def subscribe(self, name, options=None, iterator=None):
        """
        Creates a Subscription entry for the given search options identified by the given name,
        should not get any posts from the post source.
        """
        
        if iterator is None:
            iterator = self.iterator(self, options=options)
        
        iterator.init()
        
        sub = Subscription(
            source=self.source,
            name=name,
            repr=self.subscription_repr(iterator.options),
            options=iterator.options.to_json(),
            state=iterator.state.to_json()
        )
        
        self.core.add(sub)
        self.core.flush()
        
        iterator.subscription = sub
        
        return iterator
    
    def get_iterator(self, subscription):
        """
        Gets the post iterator for a specific subscription.
        
        Returns a post iterator object.
        """
        
        if self.iterator is None:
            raise NotImplementedError
        
        return self.iterator(self, subscription=subscription)

class ReverseSearchPluginBase(PluginBase):
    def search(self, options):
        """
        By extending ReverseSearchPluginBase, this method may be called with the following
        types of options objects: `{'url': 'https://...'}` and `{'path': '/home/...'}`.
        
        Reverse searching works the same as regular searching, but the RemotePosts returned
        need to include at least a thumbnail and related url.
        """
        
        if self.iterator is None:
            raise NotImplementedError
        
        options = Dynamic.from_json(options)
        
        return self.iterator(self, options=options)
    
    def create_subscription(self, name, options=None, iterator=None):
        """
        This method is out of scope for reverse search plugins.
        """
        
        raise NotImplementedError
    
    def get_iterator(self, subscription):
        """
        This method is out of scope for reverse search plugins.
        """
        
        raise NotImplementedError
    
