from typing import List, Dict, Any

class ConversationAnalytics:
    @staticmethod
    def calculate_statistics(transcript: List[Dict[str, Any]], total_audio_duration: float = 0.0) -> Dict[str, Any]:
        """
        Calculates speaker-wise conversation statistics:
        - Total speaking duration per participant
        - Number of speaking segments per participant
        - Proportion (%) of speaking time
        - Language distribution per speaker
        """
        speaker_stats = {}
        total_spoken_time = 0.0

        for seg in transcript:
            speaker = seg["speaker"]
            dur = max(0.0, seg["end"] - seg["start"])
            lang = seg.get("language", "Unknown")

            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "speaker": speaker,
                    "total_duration_seconds": 0.0,
                    "segment_count": 0,
                    "languages_used": {}
                }

            speaker_stats[speaker]["total_duration_seconds"] += dur
            speaker_stats[speaker]["segment_count"] += 1
            speaker_stats[speaker]["languages_used"][lang] = (
                speaker_stats[speaker]["languages_used"].get(lang, 0) + 1
            )

            total_spoken_time += dur

        # Format stats and calculate percentages
        formatted_speaker_stats = []
        for speaker, stats in speaker_stats.items():
            spk_dur = round(stats["total_duration_seconds"], 2)
            proportion = (spk_dur / total_spoken_time * 100.0) if total_spoken_time > 0 else 0.0
            
            # Format duration string
            mins, secs = divmod(int(spk_dur), 60)
            hrs, mins = divmod(mins, 60)
            if hrs > 0:
                dur_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                dur_str = f"{mins:02d}:{secs:02d}"

            # Primary language used by speaker
            primary_lang = max(stats["languages_used"], key=stats["languages_used"].get) if stats["languages_used"] else "English"

            formatted_speaker_stats.append({
                "speaker": speaker,
                "speaking_duration_seconds": spk_dur,
                "speaking_duration_formatted": dur_str,
                "speaking_proportion_percent": round(proportion, 1),
                "segment_count": stats["segment_count"],
                "primary_language": primary_lang,
                "languages": list(stats["languages_used"].keys())
            })

        formatted_speaker_stats.sort(key=lambda x: x["speaker"])

        return {
            "total_audio_duration_seconds": round(total_audio_duration, 2),
            "total_spoken_duration_seconds": round(total_spoken_time, 2),
            "total_speakers_count": len(formatted_speaker_stats),
            "total_segments_count": len(transcript),
            "speaker_statistics": formatted_speaker_stats
        }
