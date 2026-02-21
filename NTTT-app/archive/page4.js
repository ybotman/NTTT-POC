"use client";

import React, { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, Button, Typography, Stack, Modal, TextField, Paper } from "@mui/material";

export default function Page() {
  return <Quiz />;
}

function Quiz() {
  const [songs, setSongs] = useState([]);
  const [artists, setArtists] = useState([]);
  const [currentSong, setCurrentSong] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [basePoints, setBasePoints] = useState(100);
  const [score, setScore] = useState(100);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [quizOver, setQuizOver] = useState(false);
  const [audioStartTime, setAudioStartTime] = useState(0);
  const [sessionScore, setSessionScore] = useState(0);
  const [correctAnswer, setCorrectAnswer] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [finalMessage, setFinalMessage] = useState("");
  const [metadataLoaded, setMetadataLoaded] = useState(false);

  // Configuration states
  const [showConfigModal, setShowConfigModal] = useState(true);
  const [timeLimit, setTimeLimit] = useState(15); // default 15s
  const [numberOfSongs, setNumberOfSongs] = useState(3); // default 3 songs
  const [songsPlayed, setSongsPlayed] = useState(0);

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
    if (songs.length > 0 && artists.length > 0 && !showConfigModal) {
      loadNewSong();
    }
  }, [songs, artists, showConfigModal]);

  useEffect(() => {
    if (currentSong && artists.length > 0) {
      const correctArtist = currentSong.ArtistMaster && currentSong.ArtistMaster.trim() !== "" 
        ? currentSong.ArtistMaster 
        : "Unknown";
      setCorrectAnswer(correctArtist);

      const distractors = getDistractors(correctArtist, artists);
      const finalAnswers = shuffleArray([correctArtist, ...distractors]);
      setAnswers(finalAnswers);
    }
  }, [currentSong, artists]);

  useEffect(() => {
    if (isPlaying && !quizOver) {
      // Adjust scoring based on time limit
      // Score goes from basePoints to 0 linearly over timeLimit seconds
      const decrement = basePoints / (timeLimit * 10.0); // since interval is 0.1s

      scoreIntervalRef.current = setInterval(() => {
        setScore((prev) => Math.max(prev - decrement, 0));
      }, 100);

      timerIntervalRef.current = setInterval(() => {
        setTimeElapsed((prev) => {
          const next = prev + 0.1;
          if (next >= timeLimit) {
            finalizeQuiz();
          }
          return next;
        });
      }, 100);
    } else {
      clearIntervals();
    }
    return () => clearIntervals();
  }, [isPlaying, quizOver, basePoints, timeLimit]);

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

  const calculateBasePoints = (tLimit) => {
    if (tLimit === 10) return 100;
    if (tLimit < 10) {
      // e.g. 8s => 140 points
      return 100 + (10 - tLimit) * 20;
    } else {
      // e.g. 15s => 50 points
      return 100 - (tLimit - 10) * 10;
    }
  };

  const loadNewSong = () => {
    if (songsPlayed >= numberOfSongs) {
      // All songs played, end session
      setQuizOver(true);
      setFinalMessage("All songs played. Session complete!");
      return;
    }

    const randomIndex = Math.floor(Math.random() * songs.length);
    const song = songs[randomIndex];

    // Reset states for new round
    setTimeElapsed(0);
    setIsPlaying(false);
    setQuizOver(false);
    setSelectedAnswer(null);
    setFeedbackMessage("");
    setFinalMessage("");
    setMetadataLoaded(false);

    const startT = Math.floor(Math.random() * 90);
    setAudioStartTime(startT);

    const newBasePoints = calculateBasePoints(timeLimit);
    setBasePoints(newBasePoints);
    setScore(newBasePoints);

    setCurrentSong(song);
    console.log("Loading new song:", song.Title, "start at:", startT);
  };

  const handleMetadataLoaded = () => {
    setMetadataLoaded(true);
    if (audioRef.current) {
      audioRef.current.currentTime = audioStartTime;
    }
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
    setQuizOver(true);
    stopAudio();
    const finalPoints = Math.round(score);
    setSessionScore((prev) => prev + finalPoints);
    console.log("Quiz finalized. Score:", finalPoints);

    let msg = "";
    if (finalPoints > basePoints * 0.8) {
      msg = "Excellent job!";
    } else if (finalPoints > basePoints * 0.5) {
      msg = "Great work!";
    } else if (finalPoints > basePoints * 0.2) {
      msg = "Not bad!";
    } else {
      msg = "Better luck next time.";
    }
    setFinalMessage(msg);
  };

  const handleAnswerSelect = (answer) => {
    if (quizOver) return; 

    const userAnswer = answer.trim().toLowerCase();
    const correct = correctAnswer.trim().toLowerCase();
    if (userAnswer === correct) {
      setSelectedAnswer(answer);
      setFeedbackMessage("Correct!");
      finalizeQuiz();
    } else {
      // Wrong answer: subtract 5% of basePoints
      const penalty = basePoints * 0.05; 
      setScore((prev) => Math.max(prev - penalty, 0));
      setSelectedAnswer(answer);
      setFeedbackMessage(`Wrong answer! -${penalty.toFixed(0)} points`);
      console.log("Wrong answer chosen:", answer, "Score now:", score - penalty);
    }
  };

  const handleNextSong = () => {
    setSongsPlayed((prev) => prev + 1);
    loadNewSong();
  };

  const timerColor = () => {
    // Turn red if less than 2 seconds remain
    if (timeLimit - timeElapsed <= 2) return "red";
    return "inherit";
  };

  const handleStartConfig = () => {
    setShowConfigModal(false);
  };

  return (
    <Box sx={{ p: 4, maxWidth: 600, margin: "auto", textAlign: "center" }}>
      <Typography variant="h4" gutterBottom>
        Name That Tango Tune - MVP
      </Typography>
      <Typography variant="h6" gutterBottom>
        Session Score: {Math.round(sessionScore)}
      </Typography>

      <Modal open={showConfigModal} disableEscapeKeyDown>
        <Paper sx={{ p: 4, m: "auto", mt: 10, width: 300, textAlign: "center" }}>
          <Typography variant="h6" gutterBottom>
            Game Configuration
          </Typography>
          <TextField
            label="Time Limit (sec)"
            type="number"
            value={timeLimit}
            onChange={(e) => setTimeLimit(parseInt(e.target.value) || 10)}
            sx={{ mb: 2 }}
            fullWidth
          />
          <TextField
            label="Number of Songs"
            type="number"
            value={numberOfSongs}
            onChange={(e) => setNumberOfSongs(parseInt(e.target.value) || 1)}
            sx={{ mb: 2 }}
            fullWidth
          />
          <Button variant="contained" onClick={handleStartConfig}>
            Start
          </Button>
        </Paper>
      </Modal>

      {currentSong && !showConfigModal && (
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
                Starts at: {audioStartTime}s, plays for {timeLimit}s
              </Typography>
            </Box>
          )}

          <Typography variant="h6" sx={{ mb: 2, color: timerColor() }}>
            Time: {timeElapsed.toFixed(1)}s | Score: {Math.round(score)}
          </Typography>

          <Typography variant="body1" sx={{ mb: 2 }}>
            Who is the Artist?
          </Typography>

          {feedbackMessage && (
            <Typography
              variant="subtitle1"
              sx={{
                mb: 2,
                color: feedbackMessage.startsWith("Wrong") ? "error.main" : "success.main",
              }}
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
                Final Score for this Song: {Math.round(score)}
              </Typography>
              <Typography variant="h6" gutterBottom>
                {finalMessage}
              </Typography>
              {songsPlayed < numberOfSongs ? (
                <Button variant="contained" color="secondary" onClick={handleNextSong}>
                  Next Song
                </Button>
              ) : (
                <Typography variant="h6" gutterBottom>
                  No more songs! Your total session score is {Math.round(sessionScore)}.
                </Typography>
              )}
            </Box>
          )}
        </>
      )}
    </Box>
  );
}

Quiz.propTypes = {};

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