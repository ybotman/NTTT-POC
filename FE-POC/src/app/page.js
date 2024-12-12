// Filename: app/page.jsx
"use client";

import React, { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, Button, Typography, Stack } from "@mui/material";

// JAX - Revised Code
// Changes from previous attempt:
// 1) Ensure audio starts at the specified start time after metadata is loaded.
// 2) On wrong answer:
//    - Subtract 10 points
//    - Keep playing (do NOT stop the audio)
//    - Time and scoring continue to decrease
//    - User can guess again until correct answer is chosen or time runs out.
// 3) If correct answer is chosen, stop the audio and show final score.
// 4) If time runs out before correct guess, finalize quiz and show final score.
// 5) Show the correct answer on screen (for testing) so you can verify wrong answers.
// 6) Start with a random song and random snippet start each time.
// 7) Added console logs for debugging. Check the browser console if something seems off.

// NOTE: If user picks multiple wrong answers, each will deduct 10 points.
// We do not prevent multiple attempts. Be careful: infinite attempts can lower score a lot.
// For a real quiz, you might want to disable already chosen answers or limit attempts.

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
  const [correctAnswer, setCorrectAnswer] = useState("");

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
      setCorrectAnswer(correctOrch);
      const correctOrchObj = orchestras.find((o) => o.name === correctOrch);
      const distractors = getDistractors(correctOrchObj, orchestras);
      const finalAnswers = shuffleArray([correctOrch, ...distractors]);
      setAnswers(finalAnswers);
    }
  }, [currentSong, orchestras]);

  useEffect(() => {
    if (isPlaying && !quizOver) {
      // Decrement score every 0.1s
      scoreIntervalRef.current = setInterval(() => {
        setScore((prev) => Math.max(prev - 1, -9999));
      }, 100);

      // Track time
      timerIntervalRef.current = setInterval(() => {
        setTimeElapsed((prev) => {
          const next = prev + 0.1;
          if (next >= 10) {
            // Time's up, finalize quiz
            finalizeQuiz();
          }
          return next;
        });
      }, 100);
    } else {
      clearIntervals();
    }
    return () => clearIntervals();
  }, [isPlaying, quizOver]);

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
    console.log("Loading new song:", song.title, "start at:", startT);
  };

  const handleMetadataLoaded = () => {
    setMetadataLoaded(true);
    console.log("Metadata loaded for:", currentSong?.title);
  };

  const startAudio = () => {
    if (!currentSong || !audioRef.current) return;
    // We'll set currentTime and play after metadata is loaded
    if (metadataLoaded) {
      audioRef.current.currentTime = audioStartTime;
      audioRef.current.play().then(() => {
        setIsPlaying(true);
        console.log("Playing from time:", audioRef.current.currentTime);
      });
    } else {
      // If not loaded yet, wait for metadata
      const checkInterval = setInterval(() => {
        if (metadataLoaded && audioRef.current) {
          clearInterval(checkInterval);
          audioRef.current.currentTime = audioStartTime;
          audioRef.current.play().then(() => {
            setIsPlaying(true);
            console.log("Playing from time:", audioRef.current.currentTime);
          });
        }
      }, 100);
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setIsPlaying(false);
  };

  const finalizeQuiz = () => {
    // Called when correct answer chosen or time runs out
    setQuizOver(true);
    stopAudio();
    setSessionScore((prev) => prev + score);
    console.log("Quiz finalized. Score:", score);
  };

  const handleAnswerSelect = (answer) => {
    if (quizOver) return; // quiz already ended

    const userAnswer = answer.trim().toLowerCase();
    const correct = correctAnswer.trim().toLowerCase();
    if (userAnswer === correct) {
      // Correct answer, finalize quiz
      setSelectedAnswer(answer);
      finalizeQuiz();
    } else {
      // Wrong answer: subtract 10 points and continue
      setScore((prev) => prev - 10);
      setSelectedAnswer(answer);
      // Don't finalize, don't stop. User can try again.
      // Just log and continue.
      console.log("Wrong answer chosen:", answer, "Score now:", score - 10);
    }
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
                Starts at: {audioStartTime}s, plays for 10s (if you let it)
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

          {/* Display correct answer for testing */}
          <Typography variant="body2" sx={{ mb: 2, fontStyle: "italic" }}>
            (For Testing) Correct Answer: {correctAnswer}
          </Typography>

          <Stack spacing={2}>
            {answers.map((ans) => (
              <Button
                key={ans}
                variant={
                  selectedAnswer === ans && quizOver
                    ? ans.trim().toLowerCase() === correctAnswer.trim().toLowerCase()
                      ? "contained"
                      : "outlined"
                    : "outlined"
                }
                color={
                  selectedAnswer === ans && quizOver
                    ? ans.trim().toLowerCase() === correctAnswer.trim().toLowerCase()
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