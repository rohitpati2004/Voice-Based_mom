import numpy as np
import scipy.io.wavfile as wavfile
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SpeakerDiarizer:
    def __init__(self, num_speakers: int = None):
        self.num_speakers = num_speakers

    def diarize(self, wav_path: str) -> List[Dict[str, Any]]:
        """
        Performs speaker diarization on 16kHz mono WAV audio file.
        Returns list of segments with start, end, and speaker label ("Person 1", "Person 2", ...).
        """
        try:
            rate, data = wavfile.read(wav_path)
            if data.ndim > 1:
                data = data.mean(axis=1)
            data = data.astype(np.float32)
            if np.max(np.abs(data)) > 0:
                data = data / np.max(np.abs(data))
                
            duration = len(data) / float(rate)
            if duration <= 0:
                return []
                
            # Frame analysis for VAD & spectral feature extraction
            frame_sec = 0.5
            hop_sec = 0.25
            frame_len = int(rate * frame_sec)
            hop_len = int(rate * hop_sec)
            
            num_frames = max(1, int((len(data) - frame_len) / hop_len) + 1)
            energies = []
            features = []

            for i in range(num_frames):
                start_idx = i * hop_len
                end_idx = start_idx + frame_len
                frame = data[start_idx:end_idx]
                if len(frame) < frame_len:
                    frame = np.pad(frame, (0, frame_len - len(frame)))
                    
                energy = np.sqrt(np.mean(frame**2))
                energies.append(energy)
                
                # Simple spectral features (zero crossing rate, spectral centroid proxy)
                zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2.0 * len(frame))
                fft_mag = np.abs(np.fft.rfft(frame))
                spec_centroid = np.sum(fft_mag * np.arange(len(fft_mag))) / (np.sum(fft_mag) + 1e-8)
                features.append([energy, zcr, spec_centroid])

            energies = np.array(energies)
            features = np.array(features)
            
            # Dynamic silence thresholding
            energy_thresh = np.percentile(energies, 25) * 1.2 + 0.005
            is_speech = energies > energy_thresh
            
            # Clustering features to partition speakers
            valid_idx = np.where(is_speech)[0]
            if len(valid_idx) == 0:
                # If no clear speech energy, assign entire clip to Person 1
                return [{"start": 0.0, "end": round(duration, 2), "speaker": "Person 1"}]

            valid_feats = features[valid_idx]
            # Standardize features
            mean = np.mean(valid_feats, axis=0)
            std = np.std(valid_feats, axis=0) + 1e-8
            norm_feats = (valid_feats - mean) / std

            # Determine cluster labels (2 speakers default if not specified)
            k = self.num_speakers or 2
            if len(valid_feats) < k:
                k = 1

            if k > 1:
                from scipy.cluster.vq import kmeans2
                centroids, cluster_idx = kmeans2(norm_feats, k, minit='points')
            else:
                cluster_idx = np.zeros(len(valid_feats), dtype=int)

            frame_labels = np.full(num_frames, -1, dtype=int)
            frame_labels[valid_idx] = cluster_idx

            # Merge contiguous segments
            raw_segments = []
            curr_speaker = None
            seg_start = 0.0

            for i in range(num_frames):
                spk = frame_labels[i]
                t_start = i * hop_sec
                t_end = min(duration, t_start + frame_sec)

                if spk != curr_speaker:
                    if curr_speaker is not None and curr_speaker != -1:
                        raw_segments.append({
                            "start": round(seg_start, 2),
                            "end": round(t_start, 2),
                            "speaker_id": curr_speaker
                        })
                    curr_speaker = spk
                    seg_start = t_start

            if curr_speaker is not None and curr_speaker != -1:
                raw_segments.append({
                    "start": round(seg_start, 2),
                    "end": round(duration, 2),
                    "speaker_id": curr_speaker
                })

            # Map speaker_id to Person 1, Person 2, ...
            spk_map = {}
            for seg in raw_segments:
                sid = seg["speaker_id"]
                if sid not in spk_map:
                    spk_map[sid] = f"Person {len(spk_map) + 1}"

            final_segments = []
            for seg in raw_segments:
                final_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "speaker": spk_map[seg["speaker_id"]]
                })

            if not final_segments:
                return [{"start": 0.0, "end": round(duration, 2), "speaker": "Person 1"}]

            return final_segments

        except Exception as e:
            logger.error(f"Diarization error: {e}. Falling back to default speaker assignment.")
            return [{"start": 0.0, "end": 10.0, "speaker": "Person 1"}]
