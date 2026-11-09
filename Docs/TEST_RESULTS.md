# Play Mode test results

Unity 6000.3.28f1, Bedsit.Tests.PlayMode, run 2026-11-09

Total 37, passed 37, failed 0, skipped 0

Classes named Baked* repeat the first-person and interaction tests with the BAKED content path forced (no Sims 2 / OpenTS2 data).

| Result | Test | Time |
|---|---|---|
| Passed | AuthenticAnimationTests.EveryLibraryAnimationResolvesToAnOriginalResource | 3.1s |
| Passed | AuthenticAnimationTests.OriginalSims2AnimationVisiblyChangesACharactersPose | 4.4s |
| Passed | BakedFirstPersonTests.EachNonMirrorViewContainsAnNpc | 0.8s |
| Passed | BakedFirstPersonTests.ExactlyFourDistinctCompassViewsNinetyDegreesApart | 1.8s |
| Passed | BakedFirstPersonTests.FourTurnsReturnToOriginalOrientation | 3.3s |
| Passed | BakedFirstPersonTests.LeftTurnIsExactlyNinetyDegreesAnticlockwise | 0.9s |
| Passed | BakedFirstPersonTests.MirrorCameraIsTheEyeMirroredThroughTheGlassPlane | 0.6s |
| Passed | BakedFirstPersonTests.PlayerBodyIsNeverVisibleNorthEastWestButIsInTheMirror | 1.0s |
| Passed | BakedFirstPersonTests.RightTurnIsExactlyNinetyDegrees | 0.9s |
| Passed | BakedFirstPersonTests.StartingCameraIsFirstPerson | 0.6s |
| Passed | BakedFirstPersonTests.TurnTakesAboutAThirdOfASecond | 0.9s |
| Passed | BakedInteractionTests.EachDirectionHasItsInteractionTarget | 0.6s |
| Passed | BakedInteractionTests.EastWindowInteractionAnimatesTheNpc | 2.6s |
| Passed | BakedInteractionTests.MirrorInteractionPlaysAnAuthenticAnimationOnTheReflectedPlayer | 2.8s |
| Passed | BakedInteractionTests.NorthInteractionOpensTheDoorAndWalksIntoTheCorridorAtEyeHeight | 3.2s |
| Passed | BakedInteractionTests.WestWindowInteractionAnimatesTheNpc | 2.1s |
| Passed | FirstPersonTests.EachNonMirrorViewContainsAnNpc | 1.7s |
| Passed | FirstPersonTests.ExactlyFourDistinctCompassViewsNinetyDegreesApart | 2.7s |
| Passed | FirstPersonTests.FourTurnsReturnToOriginalOrientation | 4.0s |
| Passed | FirstPersonTests.LeftTurnIsExactlyNinetyDegreesAnticlockwise | 1.8s |
| Passed | FirstPersonTests.MirrorCameraIsTheEyeMirroredThroughTheGlassPlane | 1.6s |
| Passed | FirstPersonTests.PlayerBodyIsNeverVisibleNorthEastWestButIsInTheMirror | 1.9s |
| Passed | FirstPersonTests.RightTurnIsExactlyNinetyDegrees | 1.8s |
| Passed | FirstPersonTests.StartingCameraIsFirstPerson | 1.8s |
| Passed | FirstPersonTests.TurnTakesAboutAThirdOfASecond | 1.9s |
| Passed | InputRegionTests.CompassMathWraps | 0.0s |
| Passed | InputRegionTests.LeftEdgeTurnsLeft | 0.0s |
| Passed | InputRegionTests.MiddleAndBottomAreInert | 0.0s |
| Passed | InputRegionTests.RightEdgeTurnsRight | 0.0s |
| Passed | InputRegionTests.ScreenPixelsMapCorrectly | 0.0s |
| Passed | InputRegionTests.TopCentreInteracts | 0.0s |
| Passed | InteractionTests.EachDirectionHasItsInteractionTarget | 1.5s |
| Passed | InteractionTests.EastWindowInteractionAnimatesTheNpc | 3.7s |
| Passed | InteractionTests.MirrorInteractionPlaysAnAuthenticAnimationOnTheReflectedPlayer | 3.7s |
| Passed | InteractionTests.NorthInteractionOpensTheDoorAndWalksIntoTheCorridorAtEyeHeight | 4.1s |
| Passed | InteractionTests.WestWindowInteractionAnimatesTheNpc | 3.0s |
| Passed | WakeUpTests.WakeUpFadesInRisesAndHandsOverControl | 8.6s |

## Music POC + Act One additions (branch feature/bedroom-music-poc)

Full suite: **66 tests, 66 passed** (the 37 original + 19 `MusicEngineTests` + 3 `MusicPocSceneTests` + 7 `ActOneSceneTests`); in the last full run `FirstPersonTests.ExactlyFourDistinctCompassViewsNinetyDegreesApart` timed out once in cold content loading and passed on immediate rerun.
A cold-start `Bedsit did not become ready: creating characters` timeout (90 s) occurred in the first live-content test after a recompile in two separate runs; both passed on rerun
(not diagnosed; see Docs/music/README.md). One run also failed 11 tests because `BEDSIT_MUSIC=1` was left set in the editor process (my own capture session) - unset, all pass.

| Result | Test |
|---|---|
| Passed | MusicEngineTests.ActOnePlansOnlyTheFirstDropThenMusicPlaysOn |
| Passed | MusicEngineTests.IntroGateToleratesAFewMissesButFailingItLoopsTheIntroSection |
| Passed | MusicEngineTests.PlanFileMatchesTheTestConstants |
| Passed | MusicEngineTests.CuesBeforeTheFileStartAreRejectedNotClamped |
| Passed | MusicEngineTests.DropIsAThreeKnockDoorCueOnBeatsZeroOneTwo |
| Passed | MusicEngineTests.FailureLoopsTheIntroTwiceThenMovesOnAnywayWithoutSilence |
| Passed | MusicEngineTests.HandoverIntoAnInvalidEntryCueIsRejected |
| Passed | MusicEngineTests.HandoverNeverSchedulesFromAnAnchorAlreadyReached |
| Passed | MusicEngineTests.KnockSoundIsAShortLowThumpWithAFastDecay |
| Passed | MusicEngineTests.MixingModeProducesNoPhantomMisses |
| Passed | MusicEngineTests.MutedStemReturnsInSyncAndOnlyDuringTheMistake |
| Passed | MusicEngineTests.PadStripRegionsAreFourPadsAboveTheBottomEdgeBetweenTheTurnZones |
| Passed | MusicEngineTests.PauseFreezesTheTimelineAndSchedulingThenResumesIdentically |
| Passed | MusicEngineTests.PerfectPlayStartsTheSongFromTheOffThenCarriesOnIntoTheNextSectionAndDrops |
| Passed | MusicEngineTests.RecoveryCanReachAnotherValidAttempt |
| Passed | MusicEngineTests.RenderDemonstrationsAndAnalyseThem |
| Passed | MusicEngineTests.SecondBuildReturnsToRhythmWithoutCountingOldNotes |
| Passed | MusicEngineTests.SuppliedCueEntriesMatchTheBrief |
| Passed | MusicEngineTests.ThreeTrackSequenceAndRepeatReachEveryIntendedDrop (simulated Drop Dis / Levels) |
| Passed | MusicPocSceneTests.PadTapsInTheBottomStripDoNotTurn |
| Passed | MusicPocSceneTests.PauseFreezesTheTimelineInTheRunningGame |
| Passed | MusicPocSceneTests.TurningFollowsCompassOrderAndNeverResetsMusicOrScoring |
| Passed | ActOneSceneTests.OnlyThePlayerExistsInTheWorldAndShowsOnlyInTheMirror |
| Passed | ActOneSceneTests.TheRoomIsMessyFromEveryViewpoint |
| Passed | ActOneSceneTests.TappingMessTidiesItAwayAndTheMeterRises |
| Passed | ActOneSceneTests.TidyClicksTakePriorityOverTheTurnZones |
| Passed | ActOneSceneTests.DoorStaysShutUntilTheKnockThenOpensForAWomanIfTheRoomIsClean |
| Passed | ActOneSceneTests.AMessyRoomGetsAMan |
| Passed | ActOneSceneTests.HeadphonesGoOnAfterWakingAndTheMusicWaitsForThem |

Runtime recordings from the built exe and their signal analysis: see `Docs/music/README.md` and `Docs/music/results/`. Those are automated checks, not listening.
