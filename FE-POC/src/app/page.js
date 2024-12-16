"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import PropTypes from "prop-types";
import { Box, Button, Typography, Stack, Modal, TextField, Paper } from "@mui/material";
import Image from "next/image";

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
  const [timeLimit, setTimeLimit] = useState(15);
  const [numberOfSongs, setNumberOfSongs] = useState(3);
  const [songsPlayed, setSongsPlayed] = useState(0);

  const audioRef = useRef(null);
  const scoreIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  // Fetch and filter data
  useEffect(() => {
    Promise.all([
      fetch("/songData/djSongs.json").then((r) => r.json()),
      fetch("/songData/ArtistMaster.json").then((r) => r.json()),
    ]).then(([djSongsData, artistData]) => {
      // Filter artists to those that match the criteria
      const validArtists = artistData.filter(
        (a) => a.level === "1" && a.active === "true"
      );

      // Filter songs to have a non-blank ArtistMaster and that ArtistMaster is in valid artists
      const validSongs = djSongsData.songs.filter((song) => {
        const artistName = (song.ArtistMaster || "").trim().toLowerCase();
        if (!artistName) return false;
        // Check if artist is in validArtists
        return validArtists.some((va) => va.artist.toLowerCase() === artistName);
      });

      setSongs(validSongs);
      setArtists(validArtists);
    });
  }, []);

  const calculateBasePoints = useCallback((tLimit) => {
    if (tLimit === 10) return 100;
    if (tLimit < 10) {
      return 100 + (10 - tLimit) * 20;
    }
    return 100 - (tLimit - 10) * 10;
  }, []);

  const loadNewSong = useCallback(() => {
    if (songs.length === 0) {
      console.warn("No valid songs available.");
      return;
    }

    if (songsPlayed >= numberOfSongs) {
      // All songs played, finalize session
      setQuizOver(true);
      setFinalMessage("All songs played. Session complete!");
      return;
    }

    const randomIndex = Math.floor(Math.random() * songs.length);
    const song = songs[randomIndex];

    // Reset states for new song
    setTimeElapsed(0);
    setIsPlaying(false);
    setQuizOver(false);
    setSelectedAnswer(null);
    setFeedbackMessage("");
    setFinalMessage("");
    setMetadataLoaded(false);

    const startT = Math.floor(Math.random() * 90); // Random start time
    setAudioStartTime(startT);

    const newBasePoints = calculateBasePoints(timeLimit);
    setBasePoints(newBasePoints);
    setScore(newBasePoints);

    setCurrentSong(song);
    console.log("Loading new song:", song.Title, "start at:", startT);
  }, [songs, numberOfSongs, songsPlayed, timeLimit, calculateBasePoints]);

  useEffect(() => {
    // If configuration done, and we have songs and artists, load a new song
    if (songs.length > 0 && artists.length > 0 && !showConfigModal) {
      loadNewSong();
    }
  }, [songs, artists, showConfigModal, loadNewSong]);

  useEffect(() => {
    if (currentSong && artists.length > 0) {
      const candidateArtist = currentSong.ArtistMaster && currentSong.ArtistMaster.trim() !== ""
        ? currentSong.ArtistMaster.trim()
        : "Unknown";

      setCorrectAnswer(candidateArtist);

      const distractors = getDistractors(candidateArtist, artists);
      const finalAnswers = shuffleArray([candidateArtist, ...distractors]);
      setAnswers(finalAnswers);
    }
  }, [currentSong, artists]);

  const handleMetadataLoaded = useCallback(() => {
    setMetadataLoaded(true);
    if (audioRef.current) {
      audioRef.current.currentTime = audioStartTime;
    }
    console.log("Metadata loaded for:", currentSong?.Title);
  }, [audioStartTime, currentSong]);

  const startAudio = useCallback(() => {
    if (!currentSong || !audioRef.current) return;

    const playFromStartTime = () => {
      audioRef.current.currentTime = audioStartTime;
      audioRef.current.play().then(() => {
        setIsPlaying(true);
        console.log("Playing from time:", audioRef.current.currentTime);
      });
    };

    if (metadataLoaded) {
      playFromStartTime();
    } else {
      // Wait for metadata to load before setting the start time
      const checkInterval = setInterval(() => {
        if (metadataLoaded && audioRef.current) {
          clearInterval(checkInterval);
          playFromStartTime();
        }
      }, 100); // Check every 100ms
    }
  }, [currentSong, metadataLoaded, audioStartTime]);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setIsPlaying(false);
  }, []);

  const finalizeQuiz = useCallback(() => {
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
  }, [basePoints, score, stopAudio]);

  useEffect(() => {
    if (isPlaying && !quizOver) {
      const decrement = basePoints / (timeLimit * 10.0);

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
  }, [isPlaying, quizOver, basePoints, timeLimit, finalizeQuiz]);

  const clearIntervals = useCallback(() => {
    if (scoreIntervalRef.current) {
      clearInterval(scoreIntervalRef.current);
      scoreIntervalRef.current = null;
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
  }, []);

  const handleAnswerSelect = useCallback(
    (answer) => {
      if (quizOver) return;

      const userAnswer = answer.trim().toLowerCase();
      const correct = correctAnswer.trim().toLowerCase();
      if (userAnswer === correct) {
        setSelectedAnswer(answer);
        setFeedbackMessage("Correct!");
        finalizeQuiz();
      } else {
        const penalty = basePoints * 0.05;
        setScore((prev) => Math.max(prev - penalty, 0));
        setSelectedAnswer(answer);
        setFeedbackMessage(`Wrong answer! -${penalty.toFixed(0)} points`);
        console.log("Wrong answer chosen:", answer, "Score now:", score - penalty);
      }
    },
    [quizOver, correctAnswer, finalizeQuiz, basePoints, score]
  );

  const handleNextSong = useCallback(() => {
    setSongsPlayed((prev) => prev + 1);
    loadNewSong();
  }, [loadNewSong]);

  const timerColor = useCallback(() => {
    if (timeLimit - timeElapsed <= 2) return "red";
    return "inherit";
  }, [timeElapsed, timeLimit]);

  const handleStartConfig = useCallback(() => {
    setShowConfigModal(false);
  }, []);

  return (
    <Box sx={{ p: 0, maxWidth: 600, margin: "auto", textAlign: "center" }}>
      {/* Header with image and beta note */}
      <Box sx={{ position: "relative", width: "100%", mb: 2 }}>
        <Image
          src="/NTTTBanner.jpg"
          alt="NTTT Banner"
          width={600}
          height={100}
          style={{ width: "100%", height: "auto" }}
        />
        <Typography variant="subtitle1" sx={{ mt: 1 }}>
          (*Beta, there will be bugs)
        </Typography>
      </Box>

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
            onChange={(e) => setTimeLimit(Number(e.target.value) || 10)}
            sx={{ mb: 2 }}
            fullWidth
          />
          <TextField
            label="Number of Songs"
            type="number"
            value={numberOfSongs}
            onChange={(e) => setNumberOfSongs(Number(e.target.value) || 1)}
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
          {currentSong && (
            <audio
              ref={audioRef}
              src={currentSong.AudioUrl}
              onLoadedMetadata={handleMetadataLoaded}
            />
          )}
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

Quiz.propTypes = {
  // If you want to add prop types (optional)
};

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