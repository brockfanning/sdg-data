# -*- coding: utf-8 -*-
"""
This script makes several tweaks to the metadata to migrate it into the new
platform.

"""

import glob
import os.path
import frontmatter
from io import BytesIO

# For more readable code below.
FOLDER_META = 'meta'
FOLDER_DATA_WIDE = 'data-wide'

def update_metadata(indicator):
    with open(indicator, 'r') as f:
        post = frontmatter.load(f)

        # Figure out the reporting_status.
        reporting_status = 'notstarted'
        if 'source_url' in post.metadata and post['source_url'] is not None and post['source_url'] is not '':
            reporting_status = 'inprogress'
            if 'graph' in post.metadata and post['graph'] is not None and post['graph'] is not '':
                reporting_status = 'complete'
        post.metadata['reporting_status'] = reporting_status

        # Make sure it has a published key.
        if 'published' not in post.metadata:
            post.metadata['published'] = False

        # Make sure it has a graph_title key.
        if 'graph_title' not in post.metadata or post['graph_title'] is None or post['graph_title'] is '':
            if 'actual_indicator_available' in post.metadata and post['actual_indicator_available'] is not None:
                post.metadata['graph_title'] = post['actual_indicator_available']
            else:
                post.metadata['graph_title'] = post['title']

        # Figure out the graph_type and data_non_statistical.
        data_non_statistical = False
        graph_type = 'line'
        if 'graph' not in post.metadata or post['graph'] is None or post['graph'] is '':
            graph_type = None
            data_non_statistical = True
        elif post['graph'] is 'bar' or post['graph'] is 'binary':
            graph_type = 'bar'
        post.metadata['data_non_statistical'] = data_non_statistical
        post.metadata['graph_type'] = graph_type

    with open(indicator, 'w') as f:
        f.write(frontmatter.dumps(post))


    return True

def main():
    """Update all all of the indicators in the metadata folder."""

    status = True

    # Read all the files in the source location.
    indicators = glob.glob(FOLDER_META + "/*.md")
    print("Attempting to update " + str(len(indicators)) + " metadata files...")

    for indicator in indicators:
        status = status & update_metadata(indicator)

    return status

if __name__ == '__main__':
    if not main():
        raise RuntimeError("Failed to migrate metadata")
    else:
        print("Success")