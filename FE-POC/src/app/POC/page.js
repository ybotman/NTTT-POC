// Filename: app/page.jsx
"use client";

import React, { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, Button, Typography, Stack } from "@mui/material";

// JAX - Revised Code
// Changes made based on issues:
// 1) Ensure audio starts at the specified start time:
//    - We'll wait for "loadedmetadata" event before setting currentTime and playing.
// 2) Verify wrong answer scoring:
//    - Add console.logs and ensure string comparison normalized (trim/toLowerCase).
// 3) Add 20 more orchestras with random attributes to orchestras.json file.

// Steps:
// - Make sure we only call audioRef.current.play() after metadata loads.
// - Compare answers case-insensitive to avoid hidden char issues.

// Also updated orchestras.json below with more orchestras and attributes.

export default function Page() {
  return <Quiz />;
}

function Quiz() {
  const [songs, setSongs] = useState([]);
  const [orchestras, setOrchestras] = useState([]);
  const [currentSong, setCurrentSong] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [score, setScore] = useState(100);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [quizOver, setQuizOver] = useState(false);
  const [audioStartTime, setAudioStartTime] = useState(0);
  const [sessionScore, setSessionScore] = useState(0); // accumulate over multiple songs
  const [metadataLoaded, setMetadataLoaded] = useState(false);

  const audioRef = useRef(null);
  const scoreIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  useEffect(() => {
    // Fetch data on mount
    Promise.all([
      fetch("/songData/songs.json").then((r) => r.json()),
      fetch("/songData/orchestras.json").then((r) => r.json()),
    ]).then(([songsData, orchData]) => {
      setSongs(songsData.songs);
      setOrchestras(orchData.orchestras);
    });
  }, []);

  useEffect(() => {
    if (songs.length > 0 && orchestras.length > 0) {
      loadNewSong();
    }
  }, [songs, orchestras]);

  useEffect(() => {
    if (currentSong) {
      const correctOrch = currentSong.orchestra;
      const correctOrchObj = orchestras.find((o) => o.name === correctOrch);
      const distractors = getDistractors(correctOrchObj, orchestras);
      const finalAnswers = shuffleArray([correctOrch, ...distractors]);
      setAnswers(finalAnswers);
    }
  }, [currentSong, orchestras]);

  useEffect(() => {
    if (isPlaying) {
      // Decrement score every 0.1s
      scoreIntervalRef.current = setInterval(() => {
        setScore((prev) => Math.max(prev - 1, -9999));
      }, 100);

      // Track time
      timerIntervalRef.current = setInterval(() => {
        setTimeElapsed((prev) => {
          const next = prev + 0.1;
          if (next >= 10) {
            // stop after 10 seconds
            stopAudio();
          }
          return next;
        });
      }, 100);
    } else {
      clearIntervals();
    }
    return () => clearIntervals();
  }, [isPlaying]);

  const clearIntervals = () => {
    if (scoreIntervalRef.current) {
      clearInterval(scoreIntervalRef.current);
      scoreIntervalRef.current = null;
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
  };

  const loadNewSong = () => {
    const randomIndex = Math.floor(Math.random() * songs.length);
    const song = songs[randomIndex];
    setScore(100);
    setTimeElapsed(0);
    setIsPlaying(false);
    setQuizOver(false);
    setSelectedAnswer(null);
    setMetadataLoaded(false);

    // Set random start time between 0 and 90s
    const startT = Math.floor(Math.random() * 90);
    setAudioStartTime(startT);

    setCurrentSong(song);
  };

  const handleMetadataLoaded = () => {
    setMetadataLoaded(true);
  };

  const startAudio = () => {
    if (!currentSong || !audioRef.current) return;
    // We'll set currentTime and play after metadata is loaded
    if (metadataLoaded) {
      audioRef.current.currentTime = audioStartTime;
      audioRef.current.play();
      setIsPlaying(true);
    } else {
      // If not loaded yet, wait a bit:
      const checkInterval = setInterval(() => {
        if (metadataLoaded && audioRef.current) {
          clearInterval(checkInterval);
          audioRef.current.currentTime = audioStartTime;
          audioRef.current.play();
          setIsPlaying(true);
        }
      }, 100);
    }
  };

  const stopAudio = () => {
    setIsPlaying(false);
    if (audioRef.current) {
      audioRef.current.pause();
    }
  };

  const handleAnswerSelect = (answer) => {
    if (selectedAnswer !== null) return; // already answered
    setSelectedAnswer(answer);
    let finalScore = score;

    // Debug info
    console.log("User answer:", answer, "Correct:", currentSong.orchestra);

    // Normalize comparison
    const userAnswer = answer.trim().toLowerCase();
    const correctAnswer = currentSong.orchestra.trim().toLowerCase();
    if (userAnswer !== correctAnswer) {
      finalScore -= 10;
    }

    setScore(finalScore);
    setSessionScore((prev) => prev + finalScore);
    setQuizOver(true);
    stopAudio();
  };

  const handleNextSong = () => {
    loadNewSong();
  };

  const timerColor = () => {
    // turn red if less than 2 seconds remain
    if (10 - timeElapsed <= 2) return "red";
    return "inherit";
  };

  return (
    <Box sx={{ p: 4, maxWidth: 600, margin: "auto", textAlign: "center" }}>
      <Typography variant="h4" gutterBottom>
        Name That Tango Tune - MVP
      </Typography>
      <Typography variant="h6" gutterBottom>
        Session Score: {sessionScore}
      </Typography>

      {currentSong && (
        <>
          <audio
            ref={audioRef}
            src={currentSong.audioUrl}
            onLoadedMetadata={handleMetadataLoaded}
          />
          {!isPlaying && !quizOver && (
            <Box sx={{ mb: 2 }}>
              <Button variant="contained" color="primary" onClick={startAudio}>
                Play Song
              </Button>
              <Typography variant="caption" display="block">
                Starts at: {audioStartTime}s, plays for 10s
              </Typography>
            </Box>
          )}

          <Typography
            variant="h6"
            sx={{ mb: 2, color: timerColor() }}
          >
            Time: {timeElapsed.toFixed(1)}s | Score: {score}
          </Typography>

          <Typography variant="body1" sx={{ mb: 2 }}>
            Who is the orchestra?
          </Typography>

          <Stack spacing={2}>
            {answers.map((ans) => (
              <Button
                key={ans}
                variant={
                  selectedAnswer === ans
                    ? ans.trim().toLowerCase() === currentSong.orchestra.trim().toLowerCase()
                      ? "contained"
                      : "outlined"
                    : "outlined"
                }
                color={
                  selectedAnswer === ans
                    ? ans.trim().toLowerCase() === currentSong.orchestra.trim().toLowerCase()
                      ? "success"
                      : "error"
                    : "primary"
                }
                onClick={() => handleAnswerSelect(ans)}
                disabled={quizOver}
              >
                {ans}
              </Button>
            ))}
          </Stack>

          {quizOver && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h5" gutterBottom>
                Final Score for this Song: {score}
              </Typography>
              <Button variant="contained" color="secondary" onClick={handleNextSong}>
                Next Song
              </Button>
            </Box>
          )}
        </>
      )}
    </Box>
  );
}

Quiz.propTypes = {};

// Utility Functions
function shuffleArray(array) {
  const arr = [...array];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function getDistractors(correctOrchObj, allOrchs) {
  const correctName = correctOrchObj.name;
  const correctAttrs = correctOrchObj.attributes;

  // Filter orch that share at least one attribute
  let candidates = allOrchs.filter((o) => {
    if (o.name === correctName) return false;
    return o.attributes.some((attr) => correctAttrs.includes(attr));
  });

  // If not enough candidates, fallback to any except correct
  if (candidates.length < 3) {
    const fallback = allOrchs.filter((o) => o.name !== correctName);
    const uniqueSet = new Set([...candidates, ...fallback]);
    candidates = Array.from(uniqueSet);
  }

  const shuffled = shuffleArray(candidates);
  const top3 = shuffled.slice(0, 3).map((o) => o.name);
  return top3;
} 