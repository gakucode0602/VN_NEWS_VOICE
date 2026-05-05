/* eslint-disable react-hooks/set-state-in-effect */
import type { ChangeEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { FaPause, FaPlay, FaVolumeMute, FaVolumeUp } from "react-icons/fa";
import "../../../styles/AudioPlayer.css";

type AudioPlayerProps = {
  audioUrl: string;
  title?: string;
};

const AudioPlayer = ({ audioUrl, title }: AudioPlayerProps) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(0.5);
  const [isMuted, setIsMuted] = useState(false);
  const [hasError, setHasError] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!audioUrl) return undefined;

    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setHasError(false);

    const handleLoadedMetadata = () => {
      setDuration(audio.duration || 0);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime || 0);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    const handleError = () => {
      setHasError(true);
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    return () => {
      audio.pause();
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
      audio.src = "";
      audioRef.current = null;
    };
  }, [audioUrl]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [isMuted, volume]);

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying((prev) => !prev);
  };

  const handleProgressChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return;

    const newTime = (event.target.valueAsNumber / 100) * duration;
    setCurrentTime(newTime);
    audioRef.current.currentTime = newTime;
  };

  const handleVolumeChange = (event: ChangeEvent<HTMLInputElement>) => {
    const newVolume = event.target.valueAsNumber / 100;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    setIsMuted((prev) => !prev);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
  };

  const progressPercent = duration ? (currentTime / duration) * 100 : 0;
  const volumePercent = volume * 100;

  if (hasError) {
    return null;
  }

  return (
    <div className="audio-player">
      <div className="audio-player-top">
        <div>
          <span className="audio-eyebrow">Audio tin tức</span>
          <h5 className="audio-title">{title || "Nghe bài viết"}</h5>
        </div>
        <div className={`audio-status ${isPlaying ? "playing" : ""}`}>
          <span className="status-dot"></span>
          {isPlaying ? "Đang phát" : "Sẵn sàng"}
        </div>
      </div>

      <div className="audio-player-main">
        <button
          type="button"
          onClick={togglePlay}
          className={`audio-action ${isPlaying ? "pause" : "play"}`}
          aria-label={isPlaying ? "Tạm dừng" : "Phát"}
        >
          {isPlaying ? <FaPause /> : <FaPlay />}
        </button>

        <div className="audio-progress">
          <div className="audio-time">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={progressPercent}
            onChange={handleProgressChange}
            className="audio-progress-range audio-range"
            style={{
              background: `linear-gradient(90deg, var(--player-accent) ${progressPercent}%, #e5e7eb ${progressPercent}%)`,
            }}
          />
        </div>

        <div className="audio-volume">
          <button
            type="button"
            onClick={toggleMute}
            className="audio-icon-button"
            aria-label={isMuted ? "Bật âm thanh" : "Tắt âm thanh"}
          >
            {isMuted ? <FaVolumeMute /> : <FaVolumeUp />}
          </button>
          <input
            type="range"
            min="0"
            max="100"
            value={volumePercent}
            onChange={handleVolumeChange}
            className="audio-volume-range audio-range"
            style={{
              background: `linear-gradient(90deg, var(--player-accent) ${volumePercent}%, #e5e7eb ${volumePercent}%)`,
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;
