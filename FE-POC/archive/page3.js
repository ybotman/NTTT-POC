"use client";

import React, { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, Button, Typography, Stack } from "@mui/material";

export default function Page() {
  return <Quiz />;
}

function Quiz() {
  const [songs, setSongs] = useState([]);
  const [artists, setArtists] = useState([]);
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
  const [feedbackMessage, setFeedbackMessage] = useState(""); // New state for feedback
  const [finalMessage, setFinalMessage] = useState(""); // Final performance message

  const audioRef = useRef(null);
  const scoreIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  useEffect(() => {
    // Fetch data on mount
    Promise.all([
      fetch("/songData/djSongs.json").then((r) => r.json()),
      fetch("/songData/ArtistMaster.json").then((r) => r.json()),
    ]).then(([djSongsData, artistData]) => {
      setSongs(djSongsData.songs);
      setArtists(artistData);
    });
  }, []);

  useEffect(() => {
    if (songs.length > 0 && artists.length > 0) {
      loadNewSong();
    }
  }, [songs, artists]);

  useEffect(() => {
    if (currentSong && artists.length > 0) {
      const correctArtist = currentSong.ArtistMaster;
      setCorrectAnswer(correctArtist);

      const distractors = getDistractors(correctArtist, artists);
      const finalAnswers = shuffleArray([correctArtist, ...distractors]);
      setAnswers(finalAnswers);
    }
  }, [currentSong, artists]);

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
    setFeedbackMessage("");
    setFinalMessage("");

    // Set random start time between 0 and 90s
    const startT = Math.floor(Math.random() * 90);
    setAudioStartTime(startT);

    setCurrentSong(song);
    console.log("Loading new song:", song.Title, "start at:", startT);
  };

  const handleMetadataLoaded = () => {
    setMetadataLoaded(true);
    console.log("Metadata loaded for:", currentSong?.Title);
  };

  const startAudio = () => {
    if (!currentSong || !audioRef.current) return;
    if (metadataLoaded) {
      audioRef.current.currentTime = audioStartTime;
      audioRef.current.play().then(() => {
        setIsPlaying(true);
        console.log("Playing from time:", audioRef.current.currentTime);
      });
    } else {
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

    // Determine final message based on score
    let msg = "";
    if (score > 80) {
      msg = "Excellent job!";
    } else if (score > 50) {
      msg = "Great work!";
    } else if (score > 20) {
      msg = "Not bad!";
    } else {
      msg = "Better luck next time.";
    }
    setFinalMessage(msg);
  };

  const handleAnswerSelect = (answer) => {
    if (quizOver) return; // quiz already ended

    const userAnswer = answer.trim().toLowerCase();
    const correct = correctAnswer.trim().toLowerCase();
    if (userAnswer === correct) {
      // Correct answer, finalize quiz
      setSelectedAnswer(answer);
      setFeedbackMessage("Correct!");
      finalizeQuiz();
    } else {
      // Wrong answer: subtract 10 points and continue
      setScore((prev) => prev - 10);
      setSelectedAnswer(answer);
      setFeedbackMessage("Wrong answer! -10 points");
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
            src={currentSong.AudioUrl}
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
            Who is the Artist?
          </Typography>

          {/* Feedback message for wrong/correct answer */}
          {feedbackMessage && (
            <Typography
              variant="subtitle1"
              sx={{ mb: 2, color: feedbackMessage.startsWith("Wrong") ? "error.main" : "success.main" }}
            >
              {feedbackMessage}
            </Typography>
          )}

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
              {/* Show final performance message */}
              <Typography variant="h6" gutterBottom>
                {finalMessage}
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

function getDistractors(correctArtist, allArtists) {
  const candidates = allArtists
    .filter((a) => a.artist.toLowerCase() !== correctArtist.toLowerCase())
    .map((a) => a.artist);

  const shuffled = shuffleArray(candidates);
  return shuffled.slice(0, 3);
}