drop table if exists keypoints_name;
create table if not exists keypoints_name( id int NOT NULL,
                                    key_name text NOT NULL,
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(id)
                                );
drop table if exists keypoints_data;
create table if not exists keypoints_data( case_name text NOT NULL,
                                    frame_no int NOT NULL,
                                    key_id int NOT NULL,
                                    key_name text NOT NULL,
                                    box_id int NOT NULL,
                                    box_w real NOT NULL,
                                    box_h real NOT NULL,
                                    box_conf real NOT NULL, 
                                    x real NOT NULL,
                                    y real NOT NULL,
                                    xy_conf real NOT NULL, 
                                    norm real NOT NULL,
                                    ratio real NOT NULL,
                                    angle real NOT NULL, 
                                    inserted_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    time_epoch integer,
                                    section integer,  
                                    tag text,                               
                                    PRIMARY KEY(case_name, frame_no, key_id)
                                );
