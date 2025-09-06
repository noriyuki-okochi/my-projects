-- drop table if exists keypoints_config;
create table if not exists keypoints_config( id int NOT NULL,
                                    key_name text NOT NULL,
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(id)
                                );
-- drop table if exists frame_info;
create table if not exists frame_info( case_name text NOT NULL,
                                    img_path text,
                                    fps real NOT NULL,
                                    height int NOT NULL,
                                    width int NOT NULL,
                                    import int DEFAULT(0),
                                    start_frame int DEFAULT(0),
                                    stop_frame int DEFAULT(0),
                                    csv_path text,
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    inserted_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(case_name)
                                );
--drop table if exists tracking_data;
create table if not exists tracking_data( case_name text NOT NULL,
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
                                    eyes_span real NOT NULL, 
                                    shds_span real NOT NULL, 
                                    hips_span real NOT NULL, 
                                    hw_ratio real NOT NULL, 
                                    hw_angle real NOT NULL, 
                                    section int DEFAULT(0),
                                    completed int DEFAULT(0),  
                                    tag1 int DEFAULT(NULL),
                                    tag2 int DEFAULT(NULL),                               
                                    inserted_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    time_epoch integer,
                                    PRIMARY KEY(case_name, frame_no, key_id)
                                );
--drop table if exists act_param;
create table if not exists act_param( frame int  NOT NULL,
                                    lag int default(0),
                                    model text NOT NULL,
                                    step int NOT NULL,
                                    act int NOT NULL,
                                    sect int NOT NULL,
                                    idx int NOT NULL,
                                    val real NOT NULL,
                                    inserted_at TIMESTAMP DEFAULT(DATETIME('now','localtime')),
                                    PRIMARY KEY(frame, lag, model, step, act, sect, idx)
                                );
