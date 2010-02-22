
import reformed.data_loader
import os

TABLES = ['_core_entity', 'comment', 'user', 'severity', 'priority', 'ticket'] ## 'bookmarks', 'permission', 'user_group', 'user_group_permission', 'user_group_user']

def load(database, dir):

    this_dir = os.path.dirname(os.path.abspath(__file__))
    application_folder = os.path.join(this_dir, dir)
    data_folder = os.path.join(this_dir, "data")

    all_tables = database.metadata.sorted_tables

    for table in database.metadata.sorted_tables:
        if table.name in TABLES:
            print table.name
            flatfile = reformed.data_loader.FlatFile(
                database,
                table.name,
                os.path.join(data_folder, "%s.csv" % table.name)
            )    
            flatfile.load()