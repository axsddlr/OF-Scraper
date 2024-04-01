r"""
                                                             
 _______  _______         _______  _______  _______  _______  _______  _______  _______ 
(  ___  )(  ____ \       (  ____ \(  ____ \(  ____ )(  ___  )(  ____ )(  ____ \(  ____ )
| (   ) || (    \/       | (    \/| (    \/| (    )|| (   ) || (    )|| (    \/| (    )|
| |   | || (__     _____ | (_____ | |      | (____)|| (___) || (____)|| (__    | (____)|
| |   | ||  __)   (_____)(_____  )| |      |     __)|  ___  ||  _____)|  __)   |     __)
| |   | || (                   ) || |      | (\ (   | (   ) || (      | (      | (\ (   
| (___) || )             /\____) || (____/\| ) \ \__| )   ( || )      | (____/\| ) \ \__
(_______)|/              \_______)(_______/|/   \__/|/     \||/       (_______/|/   \__/
                                                                                      
"""
import contextlib
import logging
import math
import pathlib
import sqlite3
import arrow
from rich.console import Console

import ofscraper.db.operations_.wrapper as wrapper

console = Console()
log = logging.getLogger("shared")

mediaCreate = """
CREATE TABLE IF NOT EXISTS medias (
	id INTEGER NOT NULL, 
	media_id INTEGER, 
	post_id INTEGER NOT NULL, 
	link VARCHAR, 
	directory VARCHAR, 
	filename VARCHAR, 
	size INTEGER, 
	api_type VARCHAR, 
	media_type VARCHAR, 
	preview INTEGER, 
	linked VARCHAR, 
	downloaded INTEGER, 
	created_at TIMESTAMP, 
	hash VARCHAR,
    model_id INTEGER,
	PRIMARY KEY (id), 
	UNIQUE (media_id,model_id)
);"""
mediaALLTransition = """
SELECT  media_id,post_id,link,directory,filename,size,api_type,
media_type,preview,linked,downloaded,created_at,hash,
       CASE WHEN EXISTS (SELECT 1 FROM pragma_table_info('medias') WHERE name = 'model_id')
            THEN model_id
            ELSE NULL
       END AS model_id
FROM medias;
"""
mediaDrop = """
drop table medias;
"""
mediaUpdateAPI = """Update 'medias'
SET
media_id=?,post_id=?,linked=?,api_type=?,media_type=?,preview=?,created_at=?,model_id=?
WHERE media_id=(?) and model_id=(?);"""
mediaUpdateDownload = """Update 'medias'
SET
directory=?,filename=?,size=?,downloaded=?,hash=?
WHERE media_id=(?) and model_id=(?);"""


mediaDupeHashesMedia = """
WITH x AS (
    SELECT hash, size
    FROM medias
    WHERE hash IS NOT NULL AND size is not null and  WHERE hash IS NOT NULL AND size IS NOT NULL AND (media_type = ?)
)
)
SELECT hash
FROM x
GROUP BY hash, size
HAVING COUNT(*) > 1;
"""

mediaDupeHashes = """
WITH x AS (
    SELECT hash, size
    FROM medias
    WHERE hash IS NOT NULL AND size is not null and  WHERE hash IS NOT NULL AND size IS NOT NULL
)
)
SELECT hash
FROM x
GROUP BY hash, size
HAVING COUNT(*) > 1;
"""
mediaDupeFiles = """
SELECT filename
FROM medias
where hash=(?)
"""
mediaInsert = f"""INSERT INTO 'medias'(
media_id,post_id,link,api_type,
media_type,preview,linked,
created_at,model_id)
            VALUES (?,?,?,?,?,?,?,?,?);"""

mediaInsertFull = f"""INSERT INTO 'medias'(
media_id,post_id,link,directory,
filename,size,api_type,
media_type,preview,linked,
downloaded,created_at,hash,model_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);"""
mediaDownloadSelect= """
SELECT  
directory,filename,size
downloaded,hash
FROM medias where media_id=(?)
"""
allIDCheck = """
SELECT media_id FROM medias
"""
allDLIDCheck = """
SELECT media_id FROM medias where downloaded=(1)
"""
getTimelineMedia = """
SELECT
media_id,post_id,link,directory
filename,size,api_type,media_type
preview,linked,downloaded,created_at,hash,model_id
FROM medias where api_type=('Timeline') and model_id=(?)
"""
getArchivedMedia = """
SELECT
media_id,post_id,link,directory
filename,size,api_type,media_type
preview,linked,downloaded,created_at,hash,model_id
FROM medias where api_type=('Archived') and model_id=(?)
"""
getMessagesMedia = """
SELECT 
media_id,post_id,link,directory
filename,size,api_type,media_type
preview,linked,downloaded,created_at,hash,model_id
FROM medias where api_type=('Message') or api_type=('Messages') and model_id=(?)
"""


@wrapper.operation_wrapper_async
def create_media_table(model_id=None, username=None, conn=None):
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(mediaCreate)
        conn.commit()


@wrapper.operation_wrapper_async
def add_column_media_hash(model_id=None, username=None, conn=None):
    with contextlib.closing(conn.cursor()) as cur:
        try:
        # Check if column exists (separate statement)
            cur.execute("SELECT CASE WHEN EXISTS (SELECT 1 FROM PRAGMA_TABLE_INFO('medias') WHERE name = 'hash') THEN 1 ELSE 0 END AS alter_required;")
            alter_required = cur.fetchone()[0]  # Fetch the result (0 or 1)
            # Add column if necessary (conditional execution)
            if alter_required == 0:
                cur.execute("ALTER TABLE medias ADD COLUMN hash VARCHAR;")
                # Commit changes
            conn.commit()
            print("Successfully added 'hash' column (if it didn't exist).")
        except sqlite3.Error as e:
            conn.rollback()
            raise e  # Rollback in case of errors

@wrapper.operation_wrapper_async
def add_column_media_ID(model_id=None, username=None, conn=None):
    with contextlib.closing(conn.cursor()) as cur:
        try:
            # Check if column exists (separate statement)
            cur.execute("SELECT CASE WHEN EXISTS (SELECT 1 FROM PRAGMA_TABLE_INFO('medias') WHERE name = 'model_id') THEN 1 ELSE 0 END AS alter_required;")
            alter_required = cur.fetchone()[0]  # Fetch the result (0 or 1)

            # Add column if necessary (conditional execution)
            if alter_required == 0:
                cur.execute("ALTER TABLE medias ADD COLUMN model_id INTEGER;")

                # Commit changes
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise e  # Rollback in case of errors


@wrapper.operation_wrapper_async
def get_media_ids(model_id=None, username=None, conn=None, **kwargs) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(allIDCheck)
        return [dict(row)["media_id"] for row in cur.fetchall()]


@wrapper.operation_wrapper
def get_media_ids_downloaded(model_id=None, username=None, conn=None, **kwargs) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(allDLIDCheck)
        return [dict(row)["media_id"] for row in cur.fetchall()]


@wrapper.operation_wrapper
def get_dupe_media_hashes(
    model_id=None, username=None, conn=None, mediatype=None, **kwargs
) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        if mediatype:
            cur.execute(mediaDupeHashesMedia, [mediatype])
        else:
            cur.execute(mediaDupeHashes)
        return [dict(row)["hash"] for row in cur.fetchall()]


@wrapper.operation_wrapper
def get_dupe_media_files(
    model_id=None, username=None, conn=None, hash=None, **kwargs
) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(mediaDupeFiles, [hash])
        return [dict(row)["filename"] for row in cur.fetchall()]


@wrapper.operation_wrapper_async
def download_media_update(
    media,
    model_id=None,
    conn=None,
    filename=None,
    downloaded=None,
    hashdata=None,
    **kwargs,
):
    with contextlib.closing(conn.cursor()) as curr:
        update_media_table_via_api_helper(
            media, curr=curr, model_id=model_id, conn=conn
        )
        update_media_table_download_helper(
            media,
            model_id,
            filename=filename,
            hashdata=hashdata,
            conn=conn,
            curr=curr,
            downloaded=downloaded,
        )


@wrapper.operation_wrapper_async
def write_media_table_via_api_batch(medias, model_id=None, conn=None, **kwargs) -> list:
    with contextlib.closing(conn.cursor()) as curr:
        insertData = list(
            map(
                lambda media: [
                    media.id,
                    media.postid,
                    media.url or media.mpd,
                    media.responsetype.capitalize(),
                    media.mediatype.capitalize(),
                    media.preview,
                    media.linked,
                    media.date,
                    model_id,
                ],
                medias,
            )
        )
        curr.executemany(mediaInsert, insertData)
        conn.commit()


@wrapper.operation_wrapper_async
def write_media_table_transition(inputData, model_id=None, conn=None, **kwargs):
    with contextlib.closing(conn.cursor()) as curr:
        ordered_keys = [
        "media_id",
        "post_id",
        "link",
        "directory",
        "filename",
        "size",
        "api_type",
        "media_type",
        "preview",
        "linked",
        "downloaded",
        "created_at",
        "hash",
        "model_id"
    ]
        insertData=[tuple([data[key] for key in ordered_keys]) for data in inputData]
        curr.executemany(mediaInsertFull, insertData)
        conn.commit()


@wrapper.operation_wrapper_async
def get_all_medias_transition(model_id=None, username=None, conn=None) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(mediaALLTransition)
        conn.commit()
        data = [dict(row) for row in cur.fetchall()]
        return data



@wrapper.operation_wrapper_async
def drop_media_table(model_id=None, username=None, conn=None) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(mediaDrop)
        conn.commit()


@wrapper.operation_wrapper
def get_messages_media(conn=None, model_id=None, **kwargs) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(getMessagesMedia, [model_id])
        data = [dict(row) for row in cur.fetchall()]
        return [dict(ele,created_at=arrow.get(ele.get("created_at")).float_timestamp) for ele in data]


@wrapper.operation_wrapper
def get_archived_media(conn=None, model_id=None, **kwargs) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(getArchivedMedia, [model_id])
        data = [dict(row) for row in cur.fetchall()]
        return [dict(ele,created_at=arrow.get(ele.get("created_at")).float_timestamp) for ele in data]


@wrapper.operation_wrapper
def get_timeline_media(model_id=None, username=None, conn=None) -> list:
    with contextlib.closing(conn.cursor()) as cur:
        cur.execute(getTimelineMedia, [model_id])
        data = [dict(row) for row in cur.fetchall()]
        return [dict(ele,created_at=arrow.get(ele.get("created_at")).float_timestamp) for ele in data]


def update_media_table_via_api_helper(
    media, model_id=None, conn=None, curr=None, **kwargs
) -> list:
    insertData = [
        media.id,
        media.postid,
        media.url or media.mpd,
        media.responsetype.capitalize(),
        media.mediatype.capitalize(),
        media.preview,
        media.date,
        model_id,
        media.id,
        model_id
    ]
    curr.execute(mediaUpdateAPI, insertData)
    conn.commit()


def update_media_table_download_helper(
    media,model_id, filename=None, hashdata=None, conn=None, downloaded=None, curr=None, **kwargs
) -> list:
    prevData = curr.execute(mediaDownloadSelect, (media.id,)).fetchall()
    prevData = prevData[0] if isinstance(prevData, list) and bool(prevData) else None
    insertData = media_exist_insert_helper(
        filename=filename, hashdata=hashdata, prevData=prevData, downloaded=downloaded
    )
    insertData.extend([media.id,model_id])
    curr.execute(mediaUpdateDownload, insertData)
    conn.commit()

def media_exist_insert_helper(
    filename=None, downloaded=None, hashdata=None, prevData=None
):
    directory = None
    filename_path = None
    size = None
    if filename and pathlib.Path(filename).exists():
        directory = str(pathlib.Path(filename).parent)
        filename_path = str(pathlib.Path(filename).name)
        size = math.ceil(pathlib.Path(filename).stat().st_size)
    elif filename:
        directory = str(pathlib.Path(filename).parent)
        filename_path = str(pathlib.Path(filename).name)
    elif prevData:
        directory = prevData[0]
        filename_path = prevData[1]
        size = prevData[2]
        hashdata = prevData[3] or hashdata
    insertData = [
        directory,
        filename_path,
        size,
        downloaded,
        hashdata,
    ]
    return insertData


async def batch_mediainsert(media, **kwargs):
    curr = set(await get_media_ids(**kwargs) or [])
    mediaDict = {}
    for ele in media:
        mediaDict[ele.id] = ele
    await write_media_table_via_api_batch(
        list(filter(lambda x: x.id not in curr, mediaDict.values())), **kwargs
    )


async def modify_unique_constriant_media(model_id=None, username=None):
    data = await get_all_medias_transition(model_id=model_id, username=username)
    await drop_media_table(model_id=model_id, username=username)
    await create_media_table(model_id=model_id, username=username)
    await write_media_table_transition(data, model_id=model_id, username=username)
