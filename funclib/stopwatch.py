# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument, unused-import
'''Class with a stopwatch to calculate
the time and rates of events
This duplicates the one in opencvlib, but doesnt use the cv2 implementation
to get time.
'''


from time import sleep #for convieience
import datetime as _datetime
from collections import deque as _deque
import time as _time

#my imports
from funclib.numericslib import round_normal as _rndnorm



def _clock():
    '''
    returns absolute time in seconds since
    ticker started (usually when OS started
    '''
    # _cv2.getTickCount() / _cv2.getTickFrequency()
    return _time.time()


class _StopWatchInterval():
    '''stop watch interval'''
    SMOOTH_COEFF = 0.5

    def __init__(self, event_ticks=1, previous_interval=None, event_name=''):
        '''(str, Class:StopWatchInterval)
        '''
        self.event_name = event_name
        self.time = _clock()
        self.event_ticks = event_ticks #event could be some thing
        if previous_interval is None:
            self.running_event_ticks = self.event_ticks
        else:
            self.running_event_ticks = previous_interval.running_event_ticks + self.event_ticks
        self.previous_interval = previous_interval


    @property
    def event_rate(self):
        '''Event rate in events/ms between
        this interval and the previous one'''
        if self.previous_interval is None:
            return 0
        return (self.time - self.previous_interval.time)/self.event_ticks

    @property
    def laptime(self):
        '''Time difference in ms between
        this interval and the previous one'''
        try:
            tm = self.time - self.previous_interval.time
        except Exception as _:
            tm = 0
        return tm

    @property
    def event_rate_smoothed(self):
        '''event laptime getter, as seconds'''
        if self.previous_interval is None:
            return self.event_rate
        return _StopWatchInterval.SMOOTH_COEFF * self.previous_interval.event_rate + (1.0 - _StopWatchInterval.SMOOTH_COEFF) * self.event_rate


    def __repr__(self):
        s = 'Event %s took %.2f s, at a rate of %.2f [%.2f] per s' % (self.event_name, self.laptime, self.event_rate, self.event_rate_smoothed)
        return s


class StopWatch():
    '''
    Provides access to timed metrics using a
    stopwatch like operation and access to a
    queue of lapped times. All times are seconds.

    Provides smoothed estimates.

    Doesn't start until lap is used.

    lap:snapshot the time

    Example:
    >>>sw=stopwatch.StopWatch()
    >>>print(sw.event_rate)
    0
    >>>sw.lap()
    >>>print(sw.event_rate)
    0.0123
    '''
    def __init__(self, qsize=5, event_name=''):
        self.qsize = qsize
        self._event_name = event_name
        self._prevInterval = None
        self.reset()


    def reset(self):
        '''reset the stopwatch,
        Clears the queue, and
        sets birth_time to current system ticks
        '''
        self.Times = _deque(maxlen=self.qsize)
        self._birth_time = _clock()
        self._firstInterval = _StopWatchInterval(0, None, self._event_name)
        self._prevInterval = self._firstInterval
        self.Times.append(self._firstInterval)



    def remaining(self, n, use_smoothed=True):
        '''(int, bool) -> float
        Estimate time left in seconds using
        the smoothed event time
        Parameters
            n:number of events left
            use_smoothed: use the smoothed event, otherwise absolute

        Returns:
            float, time left in seconds

        Example:
        >>>remaining(10, use_smoothed=True)
        23.12123
        '''
        #don't use smoothed till queue is full
        try:
            x = n * self.event_rate_smoothed if use_smoothed else n * self.event_rate
        except Exception as _:
            try:
                x = n * self.event_rate_global
            except Exception as _:
                x = 0
        return x


    def remaining_global(self, n):
        '''(int) -> float
        Estimate time left in seconds using the global mean event time
        Parameters
            n:number of events left
            use_smoothed: use the smoothed event, otherwise absolute

        Returns:
            float, time left in seconds

        Example:
        >>>remaining(10, use_smoothed=True)
        23.12123
        '''
        #don't use smoothed till queue is full
        try:
            x = n * self.event_rate_global
        except Exception as _:
            x = 0
        return x


    def pretty_remaining(self, n, use_smoothed=True):
        '''(int, bool) -> str
        Return pretty formatted string of the time
        remaining

        Parameters:
            n: number of events left
            use_smoothed: use the smoothed event rates, rather than unsmoothed

        Returns:
            pretty string with an estimate of the time remaining

        Example:
        >>>SW.pretty_remaining(10, use_smoothed=True)
        4d 2h 23m
        '''
        return StopWatch.pretty_time(self.remaining(n, use_smoothed))


    def pretty_remaining_global(self, n):
        '''(int) -> str
        Return pretty formatted string of the time
        remaining, using the global mean

        Parameters:
            n: number of events left

        Returns:
            pretty string with an estimate of the time remaining

        Example:
        >>>SW.pretty_remaining_global(10)
        4d 2h 23m
        '''
        return StopWatch.pretty_time(self.remaining_global(n))



    def lap(self, event_ticks=1):
        '''(int) -> void
        Add a 'lap' time to the queue

        event_ticks
            number of events since the last lap
            Used to calculate event rates/ms
        '''
        Int = _StopWatchInterval(event_ticks, self._prevInterval, self._event_name)
        self.Times.append(Int)
        self._prevInterval = Int


    @property
    def run_time(self):
        ''' -> float
        Returns:
            Time elapsed in seconds
            since timer initialised or reset
        '''
        return _clock() -  self._birth_time


    @property
    def birth_time(self):
        '''birth_time getter'''
        return self._birth_time


    @property
    def event_rate(self):
        ''' -> float
        Get the mean event rate in seconds using
        the StopWatchInterval Queue.

        Returns:
            float of the mean event rate

        Example:
         >>>SW.event_rate
         2.1212441
        '''
        Is = list(self.Times)
        if Is:
            ts = [v.event_rate for v in Is]
            if ts:
                return sum(ts) / len(ts)
            return None
        return None


    @property
    def event_rate_smoothed(self):
        ''' -> float
        Get the mean smoothed event rate in seconds using
        the StopWatchInterval Queue.

        Returns:
            float of the mean event rate

        Example:
         >>>SW.event_rate_smoothed
         2.1212441
        '''
        Is = list(self.Times)
        if Is:
            ts = [v.event_rate_smoothed for v in Is]
            if ts:
                return sum(ts) / len(ts)
            return None
        return None



    @property
    def event_rate_global(self):
        '''(void) -> float
        Get rate over the
        lifetime of the StopWatch instance.
        '''
        t = self.Times[-1]
        assert isinstance(t, _StopWatchInterval)
        return (t.time - self._birth_time)/t.running_event_ticks


    @property
    def event_rate_last(self):
        '''(void) -> float
        Get the latest "raw" rate.
        '''
        t = self.Times[-1]
        assert isinstance(t, _StopWatchInterval)
        return t.event_rate


    @property
    def event_rate_last_smoothed(self):
        '''(void) -> float
        Get the latest smoothed rate.
        '''
        t = self.Times[-1]
        assert isinstance(t, _StopWatchInterval)
        return t.event_rate_smoothed


    @property
    def laptime(self):
        '''(void) -> float
        Get last "laptime".
        '''
        return self.Times[-1].laptime


    def __repr__(self):
        if self.Times:
            evt = 'lap' if self._event_name == '' else self._event_name
            s = str(self.Times[-1])
            s = 'Birth time %s. Last %s :%s' % (self._birth_time, evt, s)
        else:
            s = 'Birth time %s. No laps.' % self._birth_time
        return s


    @staticmethod
    def pretty_now():
        '''() -> str
        Pretty date time'''
        return _time.strftime("%Y-%m-%d %H:%M")


    @staticmethod
    def pretty_time(secs):
        '''pretty print a duration'''
        return _time_pretty(secs)



def _time_pretty(seconds):
    '''(float) -> str
    Return a prettified time interval
    for printing
    '''
    sign_string = '-' if seconds < 0 else ''
    
    if seconds < 10:
        return format(seconds, '.2f') + 's'

    seconds = abs(_rndnorm(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd %dh %dm %ds' % (sign_string, days, hours, minutes, seconds)
    if hours > 0:
        return '%s%dh %dm %ds' % (sign_string, hours, minutes, seconds)
    if minutes > 0:
        return '%s%dm %ds' % (sign_string, minutes, seconds)

    return '%s%ds' % (sign_string, seconds)