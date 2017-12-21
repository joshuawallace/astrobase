FROM python:3.6-slim-stretch

# can install directly because we now have wheels for pyeebls and astrobase
# also install ipython that will have astrobase available
RUN pip install --no-cache-dir astrobase ipython

# include the JPL ephem file so this is self-contained
RUN python -c "from astrobase import timeutils"

# setup the work directory
WORKDIR /astrobase

# the default command to run if invoked with docker run --rm -it or similar
# this just starts ipython
# to make local files in the current directory available to the docker
# container, use something like:
# docker run --rm -it -v `pwd`:/astrobase/work <container id>
CMD ["ipython"]