def process_video(video_path, output_video_path="output.mp4", start_time=None, end_time=None):
    import cv2
    import numpy as np
    from collections import defaultdict
    from deep_sort_realtime.deepsort_tracker import DeepSort
    from ultralytics import YOLO
    import json
    import os

    model = YOLO('yolov8n.pt')
    tracker = DeepSort(max_age=50, nn_budget=20, max_iou_distance=0.6)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Видео {video_path} не найдено или не может быть открыто.")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # calculating the processing boundaries in frames
    start_frame = int(start_time * fps) if start_time else 0
    end_frame = int(end_time * fps) if end_time else total_frames

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    frame_count = start_frame
    movement_stats = {"вверх": 0, "вниз": 0, "налево": 0, "направо": 0}
    tracked_ids = set()
    object_id_mapping = {}
    tracker_history = defaultdict(list)
    id_directions = {}
    dead_zone = {'x_min': 0, 'x_max': width // 2, 'y_min': 0, 'y_max': height // 4}
    people_count_history = []
    person_time_tracking = {}
    active_people = set()
    peak_density_zone = {"start_time": 0, "end_time": 0, "average_count": 0, "max_count": 0}
    density_window_size = 5 * fps

    try:
        while cap.isOpened() and frame_count < end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            current_frame_time = round(frame_count / fps, 2)
            frame_count += 1

            results = model(frame, imgsz=640, classes=[0], conf=0.6, iou=0.3)
            detections = []
            current_active_people = set()

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cx, cy = x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2

                    if dead_zone['x_min'] < cx < dead_zone['x_max'] and dead_zone['y_min'] < cy < dead_zone['y_max']:
                        continue

                    detections.append([[x1, y1, x2 - x1, y2 - y1], conf, 0])

            outputs = tracker.update_tracks(detections, frame=frame)
            current_frame_people = set()

            for output in outputs:
                if not output.is_confirmed() or output.time_since_update > 1:
                    continue

                track_id = output.track_id
                x, y, w, h = map(int, output.to_ltwh())
                cx, cy = x + w // 2, y + h // 2

                if track_id not in object_id_mapping:
                    object_id_mapping[track_id] = len(object_id_mapping) + 1

                assigned_id = object_id_mapping[track_id]
                tracked_ids.add(assigned_id)
                current_frame_people.add(assigned_id)

                if assigned_id not in person_time_tracking:
                    person_time_tracking[assigned_id] = {"enter_time": current_frame_time, "exit_time": None}

                current_active_people.add(assigned_id)

                direction = None
                if assigned_id in tracker_history:
                    prev_cx, prev_cy = tracker_history[assigned_id][-1]
                    dx, dy = cx - prev_cx, cy - prev_cy
                    if abs(dx) > abs(dy):
                        direction = "направо" if dx > 0 else "налево"
                    else:
                        direction = "вниз" if dy > 0 else "вверх"

                    if direction and assigned_id not in id_directions:
                        id_directions[assigned_id] = direction
                        movement_stats[direction] += 1

                tracker_history[assigned_id].append((cx, cy))
                if len(tracker_history[assigned_id]) > 10:
                    tracker_history[assigned_id].pop(0)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"ID: {assigned_id}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                if assigned_id in id_directions:
                    cv2.putText(frame, f"Dir: {id_directions[assigned_id]}", (x, y - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                time_spent = round(current_frame_time - person_time_tracking[assigned_id]["enter_time"], 2)
                cv2.putText(frame, f"Time: {time_spent}s", (x, y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            for person_id in active_people:
                if person_id not in current_active_people and person_time_tracking[person_id]["exit_time"] is None:
                    person_time_tracking[person_id]["exit_time"] = current_frame_time

            active_people = current_frame_people
            current_people_count = len(current_frame_people)

            people_count_history.append({"time": current_frame_time, "count": current_people_count})

            if frame_count % 30 == 0 and frame_count >= density_window_size:
                window_history = [p["count"] for p in people_count_history[-density_window_size:]]
                avg_count = sum(window_history) / len(window_history)
                max_count = max(window_history)

                if avg_count > peak_density_zone["average_count"]:
                    start_idx = len(people_count_history) - density_window_size
                    end_idx = len(people_count_history) - 1

                    peak_density_zone = {
                        "start_time": round(people_count_history[start_idx]["time"], 2),
                        "end_time": round(people_count_history[end_idx]["time"], 2),
                        "average_count": round(avg_count, 2),
                        "max_count": max_count
                    }

            cv2.putText(frame, f"People tracked: {current_people_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (255, 255, 255), 2)

            if people_count_history:
                peak = max(people_count_history, key=lambda x: x["count"])
                cv2.putText(frame, f"Peak count: {peak['count']} at {peak['time']}s", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            if peak_density_zone["average_count"] > 0:
                cv2.putText(frame, f"Peak zone: {peak_density_zone['start_time']}s - {peak_density_zone['end_time']}s",
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, f"Avg: {peak_density_zone['average_count']}, Max: {peak_density_zone['max_count']}",
                            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            out.write(frame)
            cv2.imshow("Processed Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        for person_id in person_time_tracking:
            if person_time_tracking[person_id]["exit_time"] is None:
                person_time_tracking[person_id]["exit_time"] = round(frame_count / fps, 2)

        for person_id in person_time_tracking:
            enter = person_time_tracking[person_id]["enter_time"]
            exit_ = person_time_tracking[person_id]["exit_time"]
            person_time_tracking[person_id]["time_on_screen"] = round(exit_ - enter, 2)

        if people_count_history:
            peak = max(people_count_history, key=lambda x: x["count"])
            peak_time = peak["time"]
            peak_count = peak["count"]
        else:
            peak_time = 0
            peak_count = 0

        if len(people_count_history) > density_window_size and peak_density_zone["average_count"] == 0:
            max_avg = 0
            best_start = 0
            for i in range(len(people_count_history) - density_window_size + 1):
                window = people_count_history[i:i + density_window_size]
                avg = sum(p["count"] for p in window) / len(window)
                if avg > max_avg:
                    max_avg = avg
                    best_start = i

            start_idx = best_start
            end_idx = best_start + density_window_size - 1
            window_counts = [p["count"] for p in people_count_history[start_idx:end_idx + 1]]

            peak_density_zone = {
                "start_time": round(people_count_history[start_idx]["time"], 2),
                "end_time": round(people_count_history[end_idx]["time"], 2),
                "average_count": round(sum(window_counts) / len(window_counts), 2),
                "max_count": max(window_counts)
            }

        os.makedirs("results", exist_ok=True)
        with open("results/results.json", "w", encoding="utf-8") as f:
            json.dump({
                "total_unique_people": len(tracked_ids),
                "movement_statistics": movement_stats,
                "peak_moment": {"time": peak_time, "count": peak_count},
                "peak_density_zone": peak_density_zone,
                "id_directions": id_directions,
                "source_file": os.path.basename(video_path),
                "person_time_data": person_time_tracking
            }, f, ensure_ascii=False, indent=4)

        print(f"Обработка завершена. Результаты сохранены в results/results.json и {output_video_path}.")
